"""Phase 4: AI Processing & Lazy Embeddings.

Scans CockroachDB for articles that still have a NULL `article_embedding`
(inserted raw by the Phase 3 ingestion pipeline), runs them through Groq for
bias/sentiment/credibility/topic classification, generates their vector
embedding, and writes both back to CockroachDB.

Deliberately decoupled from `services/ingestion.py` (Phase 3) so the two can
scale independently as separate AWS Lambda functions later.
"""
import asyncio
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from llm.prompts import ArticleAnalysis
from models.article import Article
from models.article_metadata import ArticleMetadata
from services.embeddings import generate_article_embedding
from services.llm_analysis import analyze_article

BATCH_SIZE = 50

# Firing every article's Groq call at once blows straight through the
# per-minute token budget (all N requests hit the 429 wall simultaneously,
# so even tenacity's backoff can't recover - they're all still competing
# for the same just-exhausted budget). Capping concurrency lets requests
# land staggered enough for the rate limit to actually replenish between
# them.
MAX_CONCURRENT_ANALYSES = 5


def _analyze_and_embed(article: Article) -> Optional[Tuple[ArticleAnalysis, list]]:
    """Runs the (blocking, network-bound) Groq + embedding calls for one article.

    Returns None if either call fails - the caller skips this article rather
    than aborting the whole batch. Pure function (no DB access) so it's safe
    to run off the main thread alongside other articles.
    """
    try:
        analysis = analyze_article(article.title, article.content)
    except Exception as exc:
        print(f"[enrichment] Skipping article {article.id} - Groq analysis failed: {exc}")
        return None

    try:
        embedding = generate_article_embedding(article.title, article.content)
    except Exception as exc:
        print(f"[enrichment] Skipping article {article.id} - embedding failed: {exc}")
        return None

    return analysis, embedding


async def _enrich_batch(pending: list) -> list:
    """Runs Groq analysis + embedding generation for every pending article
    concurrently (off-thread, bounded by MAX_CONCURRENT_ANALYSES), per the
    Phase 4 performance requirement.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)

    async def _bounded(article: Article):
        async with semaphore:
            return await asyncio.to_thread(_analyze_and_embed, article)

    return await asyncio.gather(*(_bounded(article) for article in pending))


async def run_enrichment(db: Session, batch_size: int = BATCH_SIZE) -> Dict[str, int]:
    """Processes up to `batch_size` pending articles and commits the results.

    The network-bound Groq/embedding calls run concurrently; the resulting
    DB writes happen sequentially on the main thread afterwards, since a
    SQLAlchemy Session isn't safe to share across threads.
    """
    pending = (
        db.query(Article)
        .filter(Article.article_embedding.is_(None))
        .limit(batch_size)
        .all()
    )

    results = await _enrich_batch(pending) if pending else []

    processed = 0
    for article, result in zip(pending, results):
        if result is None:
            continue
        analysis, embedding = result
        article.article_embedding = embedding
        db.add(
            ArticleMetadata(
                article_id=article.id,
                bias_score=analysis.bias_score,
                sentiment=analysis.sentiment,
                source_credibility=analysis.source_credibility,
                topic=analysis.topic,
            )
        )
        processed += 1

    db.commit()

    remaining_pending = (
        db.query(Article).filter(Article.article_embedding.is_(None)).count()
    )

    return {
        "articles_processed": processed,
        "remaining_pending": remaining_pending,
    }

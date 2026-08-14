"""Phase 3: Tier 1 News Ingestion (The Global Cache).

Fetches top headlines across a fixed set of categories from NewsAPI,
de-duplicates them via a SHA-256 content hash, and writes the raw
articles into CockroachDB. Embeddings/bias/sentiment are intentionally
left NULL here - those are generated lazily in Phase 4.
"""
import asyncio
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from core.config import settings
from models.article import Article

NEWS_API_BASE_URL = "https://newsapi.org/v2/top-headlines"

# Static category list per the Phase 3 spec.
CATEGORIES = ["politics", "technology", "business", "health", "science"]
ARTICLES_PER_CATEGORY = 20

# NewsAPI has no "politics" category - "general" is the closest fit for
# broad political coverage; every other category maps 1:1.
NEWS_API_CATEGORY_MAP = {
    "politics": "general",
    "technology": "technology",
    "business": "business",
    "health": "health",
    "science": "science",
}


def generate_article_hash(title: str, source: str, published_date: Optional[datetime]) -> str:
    """SHA-256 hash of the normalized title + hour-rounded publish time + source.

    Groups the same story reported by different outlets close together in
    time, without being so loose that unrelated articles collide.
    """
    normalized_title = re.sub(r"[^a-z0-9]", "", title.lower())
    hour_bucket = published_date.strftime("%Y%m%d%H") if published_date else "unknown"
    hash_input = f"{normalized_title}_{hour_bucket}_{source.strip().lower()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def _parse_published_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _fetch_category(client: httpx.AsyncClient, category: str) -> List[Dict[str, Any]]:
    """Fetch and normalize the top headlines for a single category."""
    params = {
        "category": NEWS_API_CATEGORY_MAP.get(category, category),
        "language": "en",
        "pageSize": ARTICLES_PER_CATEGORY,
        "apiKey": settings.NEWS_API_KEY,
    }
    try:
        response = await client.get(NEWS_API_BASE_URL, params=params, timeout=15.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        print(f"[ingestion] Failed to fetch category '{category}': {exc}")
        return []

    normalized: List[Dict[str, Any]] = []
    for item in payload.get("articles", []):
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        # Skip malformed entries (NewsAPI sometimes returns "[Removed]" stubs).
        if not title or not url or title == "[Removed]":
            continue

        content = (item.get("content") or item.get("description") or "").strip()
        source_name = ((item.get("source") or {}).get("name") or "Unknown").strip()
        published_date = _parse_published_date(item.get("publishedAt"))

        normalized.append(
            {
                "title": title,
                "content": content or title,
                "source": source_name,
                "url": url,
                "published_date": published_date,
                "category": category,
            }
        )
    return normalized


async def fetch_all_categories() -> List[Dict[str, Any]]:
    """Fetch top headlines across all configured categories concurrently."""
    async with httpx.AsyncClient() as client:
        batches = await asyncio.gather(
            *(_fetch_category(client, category) for category in CATEGORIES)
        )
    return [article for batch in batches for article in batch]


def run_ingestion(db: Session, fetched_articles: List[Dict[str, Any]]) -> Dict[str, int]:
    """De-duplicate the fetched batch against CockroachDB and insert new rows.

    Returns a summary of how many articles were fetched, ignored as
    duplicates, and actually inserted.
    """
    fetched_count = len(fetched_articles)
    if fetched_count == 0:
        return {"fetched": 0, "duplicates_ignored": 0, "inserted": 0}

    # First collapse duplicates within this batch itself (e.g. the same
    # wire story surfacing under two categories).
    seen_hashes: set = set()
    seen_urls: set = set()
    unique_batch: List[Dict[str, Any]] = []
    for article in fetched_articles:
        content_hash = generate_article_hash(
            article["title"], article["source"], article["published_date"]
        )
        if content_hash in seen_hashes or article["url"] in seen_urls:
            continue
        seen_hashes.add(content_hash)
        seen_urls.add(article["url"])
        article["content_hash"] = content_hash
        unique_batch.append(article)

    # Then check which of those already exist in CockroachDB.
    candidate_hashes = [a["content_hash"] for a in unique_batch]
    candidate_urls = [a["url"] for a in unique_batch]

    existing_hashes = {
        row[0]
        for row in db.query(Article.content_hash)
        .filter(Article.content_hash.in_(candidate_hashes))
        .all()
    }
    existing_urls = {
        row[0] for row in db.query(Article.url).filter(Article.url.in_(candidate_urls)).all()
    }

    inserted = 0
    for article in unique_batch:
        if article["content_hash"] in existing_hashes or article["url"] in existing_urls:
            continue
        db.add(
            Article(
                title=article["title"],
                content=article["content"],
                source=article["source"],
                url=article["url"],
                content_hash=article["content_hash"],
                published_date=article["published_date"],
                # article_embedding intentionally left NULL - Phase 4 (Lazy
                # Embedding Generation) fills this in.
            )
        )
        inserted += 1

    db.commit()

    return {
        "fetched": fetched_count,
        "duplicates_ignored": fetched_count - inserted,
        "inserted": inserted,
    }

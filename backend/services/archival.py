"""Phase 10: Core Article Archival Pipeline Service."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from models.article import Article
from models.article_metadata import ArticleMetadata
from services.s3_storage import format_archive_key, format_article_payload, upload_article_to_s3
from services.db_cleanup import nullify_article_storage

logger = logging.getLogger(__name__)


def archive_stale_articles(
    db: Session,
    days_cutoff: int = 30,
    batch_limit: int = 100
) -> Dict[str, Any]:
    """
    Sweeps CockroachDB for articles published > `days_cutoff` days ago.
    Offloads their full payload into S3 and nullifies their vectors in CockroachDB.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_cutoff)

    # Query stale articles that still have vector embeddings or full content stored
    stale_query = (
        select(Article, ArticleMetadata)
        .outerjoin(ArticleMetadata, Article.id == ArticleMetadata.article_id)
        .where(Article.published_date < cutoff_date)
        .where(
            or_(
                Article.article_embedding.isnot(None),
                Article.content.isnot(None)
            )
        )
        .limit(batch_limit)
    )

    results = db.execute(stale_query).all()

    processed_count = len(results)
    archived_count = 0
    errors: List[str] = []

    for article, metadata in results:
        try:
            # 1. Format Payload & S3 Key
            s3_key = format_archive_key(str(article.id), article.published_date)
            payload = format_article_payload(article, metadata)

            # 2. Upload Payload to S3 Cold Storage
            upload_res = upload_article_to_s3(payload, s3_key)

            if upload_res.get("status") in ["uploaded", "simulated"]:
                s3_url = upload_res.get("s3_url", f"s3://amplinews-archive-store/{s3_key}")

                # 3. CockroachDB Cleanup: Nullify Vector & Content
                cleaned = nullify_article_storage(db, article.id, s3_url)
                if cleaned:
                    archived_count += 1
                else:
                    errors.append(f"DB cleanup failed for article {article.id}")
            else:
                errors.append(f"S3 upload failed for article {article.id}")

        except Exception as exc:
            logger.error(f"[Archival Service] Error archiving article {article.id}: {exc}", exc_info=True)
            errors.append(f"Error archiving article {article.id}: {str(exc)}")

    return {
        "status": "success" if not errors else "partial",
        "days_cutoff": days_cutoff,
        "processed_count": processed_count,
        "archived_count": archived_count,
        "errors": errors,
    }

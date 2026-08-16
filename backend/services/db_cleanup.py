"""Phase 10: CockroachDB Memory & Vector Index Cleanup Service."""
import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from models.article import Article

logger = logging.getLogger(__name__)


def nullify_article_storage(
    db: Session,
    article_id: uuid.UUID,
    s3_archive_url: str
) -> bool:
    """
    Cleans up heavy storage in CockroachDB after verifying successful S3 upload:
    1. Nullifies `article_embedding` vector (shrinks HNSW index).
    2. Nullifies `content` text column (saves transactional storage).
    3. Saves `s3_archive_url` pointer.
    """
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.warning(f"[DB Cleanup] Article {article_id} not found.")
            return False

        article.article_embedding = None
        article.content = None
        article.s3_archive_url = s3_archive_url

        db.commit()
        logger.info(f"[DB Cleanup] Successfully offloaded article {article_id} vector & content to {s3_archive_url}")
        return True

    except Exception as exc:
        db.rollback()
        logger.error(f"[DB Cleanup] Failed to cleanup CockroachDB for article {article_id}: {exc}")
        return False

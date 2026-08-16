"""Phase 9: LangGraph Agent Nodes for AmpliNews Daily Digest Machine."""
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from db.session import SessionLocal
from models.user_profile import UserProfile
from models.reading_history import ReadingHistory
from models.article import Article
from models.article_metadata import ArticleMetadata
from agent.state import DigestState
from core.config import settings

logger = logging.getLogger(__name__)


def retrieve_context_node(state: DigestState) -> DigestState:
    """
    Node 1: RetrieveContextNode
    Fetches the user's profile and last 7 days of reading history from CockroachDB.
    """
    user_id_str = state.get("user_id")
    if not user_id_str:
        state["status"] = "error"
        state["error_message"] = "Missing user_id in state"
        return state

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        state["status"] = "error"
        state["error_message"] = f"Invalid user_id format: {user_id_str}"
        return state

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
        if not profile:
            state["status"] = "error"
            state["error_message"] = f"User profile not found for user_id {user_id_str}"
            return state

        # Fetch last 7 days of reading history
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        history_query = (
            select(ReadingHistory, Article, ArticleMetadata)
            .join(Article, ReadingHistory.article_id == Article.id)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .where(ReadingHistory.user_id == user_uuid)
            .where(ReadingHistory.timestamp >= cutoff)
            .order_by(ReadingHistory.timestamp.desc())
        )

        results = db.execute(history_query).all()

        history_items: List[Dict[str, Any]] = []
        for rh, art, meta in results:
            history_items.append({
                "history_id": str(rh.id),
                "article_id": str(art.id),
                "title": art.title,
                "source": art.source,
                "topic": meta.topic or "General",
                "bias_score": meta.bias_score if meta.bias_score is not None else 0.0,
                "read_duration": rh.read_duration_seconds or 0,
                "liked": rh.liked or False,
                "rejected_biased": rh.rejected_biased or False,
                "timestamp": rh.timestamp.isoformat() if rh.timestamp else None,
            })

        state["reading_history"] = history_items
        # Fallback email if user profile has no explicit email field
        state["user_email"] = getattr(profile, "email", None) or settings.AWS_SES_SENDER_EMAIL
        state["status"] = "pending"
        logger.info(f"[RetrieveContextNode] Retrieved {len(history_items)} history items for user {user_id_str}")

    except Exception as e:
        logger.error(f"[RetrieveContextNode] Error fetching context: {e}", exc_info=True)
        state["status"] = "error"
        state["error_message"] = str(e)
    finally:
        db.close()

    return state

import uuid
import math
import logging
from typing import List, Optional
from db.session import SessionLocal
from models.user_profile import UserProfile
from models.article import Article

logger = logging.getLogger(__name__)

def calculate_learning_rate(read_duration_seconds: int, liked: bool, rejected_biased: bool) -> float:
    """
    Determines learning rate L according to engagement criteria:
    - Clicked "Too Biased": L = -0.15 (shift away)
    - Clicked "Like": L = 0.10
    - Read for >= 60 seconds: L = 0.05
    - Bounce (< 5s / unengaged): L = 0.0
    """
    if rejected_biased:
        return -0.15
    if liked:
        return 0.10
    if read_duration_seconds >= 60:
        return 0.05
    return 0.0

def compute_shifted_vector(user_vector: List[float], article_vector: List[float], learning_rate: float) -> List[float]:
    """
    Calculates U_new = U + (A - U) * L and normalizes U_new to unit L2 length.
    """
    if len(user_vector) != len(article_vector):
        raise ValueError(f"Vector dimensions do not match: user ({len(user_vector)}) vs article ({len(article_vector)})")

    # Shift calculation
    shifted = [u + (a - u) * learning_rate for u, a in zip(user_vector, article_vector)]

    # L2 Normalization
    magnitude = math.sqrt(sum(x * x for x in shifted))
    if magnitude > 0:
        normalized = [x / magnitude for x in shifted]
    else:
        normalized = shifted

    return normalized

def shift_user_vector_task(
    user_id: uuid.UUID,
    article_id: uuid.UUID,
    read_duration_seconds: int,
    liked: bool,
    rejected_biased: bool
) -> None:
    """
    Background worker function to update user interest_embedding in CockroachDB.
    """
    learning_rate = calculate_learning_rate(read_duration_seconds, liked, rejected_biased)
    if learning_rate == 0.0:
        logger.info(f"Learning rate is 0.0 for user {user_id} on article {article_id}. Skipping vector update.")
        return

    db = SessionLocal()
    try:
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile or user_profile.interest_embedding is None:
            logger.warning(f"User profile {user_id} not found or missing interest_embedding.")
            return

        article = db.query(Article).filter(Article.id == article_id).first()
        if not article or article.article_embedding is None:
            logger.warning(f"Article {article_id} not found or missing article_embedding.")
            return

        # Convert pgvector Vector object/array to python float list if necessary
        user_vec = [float(x) for x in list(user_profile.interest_embedding)]
        article_vec = [float(x) for x in list(article.article_embedding)]

        new_interest_vec = compute_shifted_vector(user_vec, article_vec, learning_rate)

        user_profile.interest_embedding = new_interest_vec
        db.commit()
        logger.info(f"Successfully shifted interest_embedding for user {user_id} (L={learning_rate})")
    except Exception as e:
        db.rollback()
        logger.error(f"Error shifting user vector for user {user_id}: {e}", exc_info=True)
    finally:
        db.close()

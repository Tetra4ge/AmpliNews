from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.deps import get_current_user
from db.session import get_db
from schemas.user import UserProfileResponse
from models.user_profile import UserProfile
from models.reading_history import ReadingHistory
from models.article_metadata import ArticleMetadata
import uuid

router = APIRouter()

@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_uuid = uuid.UUID(current_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format in token")

    # Fetch User Profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Calculate Reading Stats
    total_articles_read = db.query(func.count(ReadingHistory.id)).filter(ReadingHistory.user_id == user_uuid).scalar()

    # Find Most Read Topic (Join ReadingHistory -> ArticleMetadata)
    most_read_topic = db.query(ArticleMetadata.topic)\
        .join(ReadingHistory, ReadingHistory.article_id == ArticleMetadata.article_id)\
        .filter(ReadingHistory.user_id == user_uuid)\
        .group_by(ArticleMetadata.topic)\
        .order_by(func.count(ReadingHistory.id).desc())\
        .first()

    return UserProfileResponse(
        user_id=profile.user_id,
        baseline_political_leaning=profile.baseline_political_leaning,
        total_articles_read=total_articles_read or 0,
        most_read_topic=most_read_topic[0] if most_read_topic else None
    )

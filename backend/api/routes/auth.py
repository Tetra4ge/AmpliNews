from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.deps import get_current_user
from db.session import get_db
from schemas.user import UserSyncRequest
from models.user_profile import UserProfile
from services.embeddings import generate_user_embedding
import uuid

router = APIRouter()

@router.post("/sync", status_code=status.HTTP_200_OK)
def sync_user(
    request: UserSyncRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Syncs the user profile into CockroachDB.
    - New user: creates a profile with an initial 384d vector based on their selected topics.
    - Existing user: regenerates the interest vector from the newly selected topics and
      updates the baseline leaning, so this endpoint also powers "edit preferences".
    """
    try:
        user_uuid = uuid.UUID(current_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format in token")

    # Regenerate the interest embedding from the (possibly updated) topic selection.
    interest_embedding = generate_user_embedding(request.selected_topics)

    existing_user = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
    if existing_user:
        existing_user.interest_embedding = interest_embedding
        existing_user.baseline_political_leaning = request.baseline_leaning
        db.commit()
        return {"message": "User preferences updated"}

    # Create new profile
    new_profile = UserProfile(
        user_id=user_uuid,
        interest_embedding=interest_embedding,
        baseline_political_leaning=request.baseline_leaning
    )

    db.add(new_profile)
    db.commit()

    return {"message": "User profile initialized successfully"}

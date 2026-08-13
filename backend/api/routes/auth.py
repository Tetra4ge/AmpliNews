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
    If the user doesn't exist, it generates an initial 384d vector based on their selected topics.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format in token")

    # Check if user already exists (Idempotency)
    existing_user = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
    if existing_user:
        return {"message": "User already synced"}

    # Generate initial interest embedding via HuggingFace
    interest_embedding = generate_user_embedding(request.selected_topics)

    # Create new profile
    new_profile = UserProfile(
        user_id=user_uuid,
        interest_embedding=interest_embedding,
        baseline_political_leaning=request.baseline_leaning
    )

    db.add(new_profile)
    db.commit()

    return {"message": "User profile initialized successfully"}

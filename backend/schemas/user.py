from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class UserSyncRequest(BaseModel):
    selected_topics: List[str] = Field(..., description="List of topics the user is interested in")
    baseline_leaning: float = Field(0.0, ge=-1.0, le=1.0, description="User's initial political leaning (-1.0 to 1.0)")

class UserProfileResponse(BaseModel):
    user_id: uuid.UUID
    baseline_political_leaning: float
    total_articles_read: int
    most_read_topic: Optional[str] = None

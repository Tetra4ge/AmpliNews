import uuid
from pydantic import BaseModel, Field

class ReadPayload(BaseModel):
    article_id: uuid.UUID = Field(..., description="UUID of the article read")
    read_duration_seconds: int = Field(0, ge=0, description="Duration spent reading article in seconds")
    liked: bool = Field(False, description="Explicit feedback: User liked article")
    rejected_biased: bool = Field(False, description="Explicit feedback: User flagged article as too biased")

class ReadResponse(BaseModel):
    status: str = "logged"
    message: str = "Interaction logged successfully"

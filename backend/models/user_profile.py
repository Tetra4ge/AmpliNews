import uuid
from sqlalchemy import Column, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .base import Base

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    # Maps to Supabase Auth ID
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Used to find relevant articles for the user
    interest_embedding = Column(Vector(1536))
    
    # Baseline leaning: -1.0 (Extreme Left) to 1.0 (Extreme Right)
    baseline_political_leaning = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

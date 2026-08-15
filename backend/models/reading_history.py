import uuid
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class ReadingHistory(Base):
    __tablename__ = 'reading_history'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    
    read_duration_seconds = Column(Integer)
    liked = Column(Boolean, default=False)
    rejected_biased = Column(Boolean, default=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

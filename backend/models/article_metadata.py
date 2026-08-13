import uuid
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ArticleMetadata(Base):
    __tablename__ = 'article_metadata'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    
    # Range is -1.0 (Extreme Left) to +1.0 (Extreme Right)
    bias_score = Column(Float)
    
    sentiment = Column(String(50))
    
    # Range 0.0 to 1.0
    source_credibility = Column(Float)
    
    topic = Column(String(100))

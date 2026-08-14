import uuid
from sqlalchemy import Column, String, Float
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class PerspectivePair(Base):
    __tablename__ = 'perspective_pairs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Maps two opposing articles
    article_id_a = Column(UUID(as_uuid=True), nullable=False)
    article_id_b = Column(UUID(as_uuid=True), nullable=False)
    
    topic = Column(String(100))
    similarity_score = Column(Float)

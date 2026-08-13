import uuid
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .base import Base

class Article(Base):
    __tablename__ = 'articles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    published_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Tier 1 Hot Cache: 1536-dimensional vector for OpenAI/Groq embeddings
    article_embedding = Column(Vector(1536))
    
    # HNSW Index for fast vector similarity search using cosine distance
    __table_args__ = (
        Index(
            'ix_articles_embedding_hnsw',
            'article_embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'article_embedding': 'vector_cosine_ops'}
        ),
    )

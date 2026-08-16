import uuid
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
# pyrefly: ignore [missing-import]
from pgvector.sqlalchemy import Vector
from .base import Base

class Article(Base):
    __tablename__ = 'articles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    published_date = Column(DateTime(timezone=True), server_default=func.now())

    # SHA-256 hash of (normalized title + hour-rounded publish time + source),
    # used to de-duplicate the same story reported by multiple outlets.
    content_hash = Column(String(64), nullable=False, unique=True)

    # Pointer to AWS S3 cold storage archive payload for articles > 30 days old
    s3_archive_url = Column(String(1024), nullable=True)

    # Tier 1 Hot Cache: 384-dimensional vector for HuggingFace all-MiniLM-L6-v2
    article_embedding = Column(Vector(384))


    # HNSW Index for fast vector similarity search using cosine distance
    __table_args__ = (
        Index(
            'ix_articles_embedding_hnsw',
            'article_embedding',
            postgresql_using='hnsw',
            postgresql_ops={'article_embedding': 'vector_cosine_ops'}
        ),
    )

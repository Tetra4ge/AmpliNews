import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class AgentMemory(Base):
    __tablename__ = 'agent_memory'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False)
    
    # e.g., "rejected_bias_threshold"
    memory_key = Column(String(100))
    
    # e.g., "User consistently swipes away articles with a bias > 0.8"
    memory_value = Column(Text)

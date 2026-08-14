import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Single source of truth for backend environment configuration."""

    # Server
    PORT: int = int(os.environ.get("PORT", 8000))
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    # CockroachDB Serverless (pgvector enabled)
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # Supabase acts strictly as the Identity Provider (IdP). We never store
    # passwords/emails - only the JWT `sub` (user_id) to link memory layers.
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_JWT_SECRET: str = os.environ.get("SUPABASE_JWT_SECRET", "")
    # Supabase issues HS256 JWTs with this audience by default.
    SUPABASE_JWT_AUDIENCE: str = os.environ.get("SUPABASE_JWT_AUDIENCE", "authenticated")
    JWT_ALGORITHM: str = "HS256"

    # Embedding model (HuggingFace all-MiniLM-L6-v2, 384 dimensions)
    HF_API_KEY: str = os.environ.get("HF_API_KEY", "")

    # LLM & Agent Orchestration (Groq - Phase 4)
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")

    # News Ingestion (Tier 1 Cache - Phase 3)
    NEWS_API_KEY: str = os.environ.get("NEWS_API_KEY", "")

    # Static secret required to hit the manual admin ingestion trigger.
    ADMIN_SECRET_KEY: str = os.environ.get("ADMIN_SECRET_KEY", "")


settings = Settings()

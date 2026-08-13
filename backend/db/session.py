import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# We expect the URL in the format postgresql://user:pass@host:26257/defaultdb?sslmode=verify-full
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Use a dummy URL for now so that the code doesn't crash when running migrations without a URL
    DATABASE_URL = "postgresql://dummy:dummy@localhost:26257/defaultdb?sslmode=verify-full"

# CockroachDB specifically needs postgresql+psycopg2 driver if using psycopg2
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# CockroachDB Serverless handles connection drops, pool_pre_ping is required
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database connection and create the vector extension if it doesn't exist.
    Run this when the application starts or during migrations.
    """
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # We must use autocommit for CREATE EXTENSION
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                text("CREATE EXTENSION IF NOT EXISTS vector;")
            )
            conn.commit()
    except Exception as e:
        print(f"Warning: Could not create vector extension: {e}")

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.session import engine

def reset_db():
    print("Dropping existing tables to reset schema...")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS reading_history CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS article_metadata CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS agent_memory CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS perspective_pairs CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS user_profiles CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS articles CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
    print("Database reset successfully.")

if __name__ == "__main__":
    reset_db()

import os
import sys
import uuid
from sqlalchemy import create_engine, text

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import DATABASE_URL, init_db

def test_connection():
    if "dummy" in DATABASE_URL:
        print("Using dummy DATABASE_URL. Please set the real DATABASE_URL in .env to test the connection.")
        return

    print(f"Connecting to database at {DATABASE_URL.split('@')[-1]}...")
    engine = create_engine(DATABASE_URL)
    
    try:
        # 1. Initialize DB and create pgvector extension
        init_db()
        print("✅ Database connection successful and vector extension ensured.")
        
        # 2. Test pgvector operations
        with engine.connect() as conn:
            # We don't have tables created yet if migrations haven't run, 
            # but we can test if the vector type exists and can compute distance.
            # We will compute the cosine distance (<=>) between two identical vectors
            # The result should be 0.
            result = conn.execute(
                text("SELECT '[1, 0, 0]'::vector <=> '[1, 0, 0]'::vector;")
            ).scalar()
            
            if result == 0.0:
                print("✅ pgvector extension is working correctly! Vector distance computed successfully.")
            else:
                print(f"❌ pgvector test failed. Expected 0.0, got {result}")
                
    except Exception as e:
        print(f"❌ Connection or vector test failed: {e}")

if __name__ == "__main__":
    test_connection()

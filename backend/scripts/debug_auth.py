import os
import sys
import uuid
import traceback
from fastapi.testclient import TestClient

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from scripts.test_auth import create_mock_jwt

client = TestClient(app)

def run_debug():
    token, user_id = create_mock_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "selected_topics": ["Tech", "AI", "Startup"],
        "baseline_leaning": 0.5
    }
    
    print("\n--- Sending request to /api/auth/sync ---")
    try:
        response = client.post("/api/auth/sync", headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print("Caught an exception within FastAPI:")
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()

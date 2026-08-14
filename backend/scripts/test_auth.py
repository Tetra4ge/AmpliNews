import os
import sys
import uuid
import requests
from jose import jwt
from datetime import datetime, timedelta

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.security import settings

# Wait for server to start if running locally
BASE_URL = "http://localhost:8000"


def create_mock_jwt() -> tuple[str, str]:
    """Creates a mock Supabase JWT for testing."""
    test_user_id = str(uuid.uuid4())
    payload = {
        "aud": settings.SUPABASE_JWT_AUDIENCE,
        "sub": test_user_id,
        "email": "test@amplinews.com",
        "role": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    print(f"Generated mock JWT for user: {test_user_id}")
    return token, test_user_id


def test_missing_token():
    """Validation Step 1: a request with no token MUST return 401."""
    print("\n--- Testing missing token -> expect 401 ---")
    response = requests.get(f"{BASE_URL}/api/user/profile")
    print(f"Status: {response.status_code}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_invalid_token():
    """Validation Step 1: a request with a garbage/invalid token MUST return 401."""
    print("\n--- Testing invalid token -> expect 401 ---")
    headers = {"Authorization": "Bearer not-a-real-jwt"}
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"Status: {response.status_code}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_sync_endpoint(token: str):
    """Validation Step 2 & 3: a valid JWT is accepted and the user row is created."""
    print("\n--- Testing POST /api/auth/sync ---")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "selected_topics": ["Tech", "AI", "Startup"],
        "baseline_leaning": 0.5,
    }

    response = requests.post(f"{BASE_URL}/api/auth/sync", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except Exception:
        print(f"Raw Response: {response.text}")
    assert response.status_code == 200


def test_sync_idempotency(token: str):
    """Validation Step 4: hitting /sync twice must not error or overwrite the vector."""
    print("\n--- Testing POST /api/auth/sync idempotency (2nd call) ---")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "selected_topics": ["Different", "Topics", "This Time"],
        "baseline_leaning": -0.9,
    }

    response = requests.post(f"{BASE_URL}/api/auth/sync", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json().get("message") == "User already synced"


def test_profile_endpoint(token: str):
    print("\n--- Testing GET /api/user/profile ---")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200


if __name__ == "__main__":
    try:
        print("Starting Auth Tests...")

        test_missing_token()
        test_invalid_token()

        token, user_id = create_mock_jwt()

        test_sync_endpoint(token)
        test_sync_idempotency(token)
        test_profile_endpoint(token)

        print("\nAll auth tests passed!")
    except requests.exceptions.ConnectionError:
        print("Could not connect to the API. Is FastAPI running on http://localhost:8000 ?")
    except Exception as e:
        print(f"Test failed: {e}")

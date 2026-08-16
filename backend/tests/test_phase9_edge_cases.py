"""Phase 9 Edge-Case & API Integration Test Suite for AmpliNews Agent."""
import os
import sys
import unittest
import uuid
import math

# Add backend root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from db.session import SessionLocal
from agent.state import DigestState
from agent.nodes import retrieve_context_node, analyze_bias_node, synthesize_digest_node
from services.vector_service import calculate_learning_rate, compute_shifted_vector
from services.ingestion import generate_article_hash
from datetime import datetime


class TestPhase9EdgeCases(unittest.TestCase):

    def test_07_invalid_user_id_handling(self):
        """Test Scenario 7: Malformed user_id handling in LangGraph nodes."""
        print("\n🧪 Test 7: Malformed User ID Error Handling")
        state: DigestState = {
            "user_id": "invalid-uuid-string-12345",
            "user_email": None,
            "reading_history": [],
            "echo_chamber_risk": 0.0,
            "echo_chamber_detected": False,
            "dominant_bias": "Balanced",
            "top_topic": None,
            "selected_articles": [],
            "contrarian_articles": [],
            "final_email_html": "",
            "status": "pending",
            "error_message": None,
        }

        res = retrieve_context_node(state)
        self.assertEqual(res["status"], "error")
        self.assertIn("Invalid user_id format", res["error_message"])
        print(f"✅ Invalid User ID Handled Gracefully: {res['error_message']}")

    def test_08_vector_shift_l2_normalization(self):
        """Test Scenario 8: Math verification for vector shift & L2 unit normalization."""
        print("\n🧪 Test 8: Vector Shift & L2 Normalization Math Verification")
        user_vec = [0.5, 0.5, 0.5, 0.5]
        article_vec = [1.0, 0.0, 0.0, 1.0]

        # Test positive shift (liked: L = 0.10)
        lr_like = calculate_learning_rate(30, True, False)
        self.assertEqual(lr_like, 0.10)

        new_vec = compute_shifted_vector(user_vec, article_vec, lr_like)
        magnitude = math.sqrt(sum(x * x for x in new_vec))
        self.assertAlmostEqual(magnitude, 1.0, places=5)

        # Test negative shift (too biased: L = -0.15)
        lr_biased = calculate_learning_rate(30, False, True)
        self.assertEqual(lr_biased, -0.15)

        neg_vec = compute_shifted_vector(user_vec, article_vec, lr_biased)
        neg_magnitude = math.sqrt(sum(x * x for x in neg_vec))
        self.assertAlmostEqual(neg_magnitude, 1.0, places=5)
        print("✅ L2 Vector Normalization & Learning Rate Math Verified (Magnitude = 1.0000)!")

    def test_09_ingestion_hash_deduplication(self):
        """Test Scenario 9: SHA-256 Article Deduplication Hashing."""
        print("\n🧪 Test 9: Article Content Hash Deduplication Test")
        now = datetime.now()
        h1 = generate_article_hash("Breaking: Tech Regulation Passed", "BBC News", now)
        h2 = generate_article_hash("BREAKING: tech regulation passed!", "BBC News", now)
        h3 = generate_article_hash("Different Headline Entirely", "BBC News", now)

        self.assertEqual(h1, h2, "Normalized title and source must yield identical SHA-256 hash")
        self.assertNotEqual(h1, h3, "Different titles must yield distinct hashes")
        print("✅ Article SHA-256 Hash Deduplication Logic Verified!")

    def test_10_fastapi_health_endpoint(self):
        """Test Scenario 10: FastAPI Server Health & Routing Endpoints."""
        print("\n🧪 Test 10: FastAPI Server Endpoint Route Verification")
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("status"), "up")
        print(f"✅ FastAPI Health Endpoint Verified! Response: {data}")

    def test_11_llm_fallback_html_generator(self):
        """Test Scenario 11: Groq LLM Fallback HTML Synthesis Engine."""
        print("\n🧪 Test 11: LLM Synthesis Fallback HTML Generator")
        state: DigestState = {
            "user_id": "99999999-9999-9999-9999-999999999999",
            "user_email": "test@amplinews.com",
            "reading_history": [],
            "echo_chamber_risk": 0.75,
            "echo_chamber_detected": True,
            "dominant_bias": "Left",
            "top_topic": "Politics",
            "selected_articles": [
                {
                    "title": "Standard News Story",
                    "source": "Reuters",
                    "url": "https://reuters.com/1",
                    "content_summary": "Summary text",
                    "match_percentage": 92.5,
                    "bias": "Center"
                }
            ],
            "contrarian_articles": [
                {
                    "title": "Contrarian Perspective Story",
                    "source": "Wall Street Journal",
                    "url": "https://wsj.com/1",
                    "content_summary": "Opposing view summary",
                    "match_percentage": 88.0,
                    "bias": "Right"
                }
            ],
            "final_email_html": "",
            "status": "pending",
            "error_message": None,
        }

        res = synthesize_digest_node(state)
        self.assertEqual(res["status"], "success")
        self.assertIn("ampli", res["final_email_html"].lower())
        self.assertIn("perspective check", res["final_email_html"].lower())
        print("✅ HTML Synthesis Engine Verified!")


if __name__ == "__main__":
    unittest.main()

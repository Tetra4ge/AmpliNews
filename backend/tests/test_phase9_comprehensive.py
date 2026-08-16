"""Comprehensive Phase 9 Multi-Scenario Test Suite for AmpliNews Agent."""
import os
import sys
import unittest
import uuid
from datetime import datetime, timezone

# Add backend root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from models.user_profile import UserProfile
from models.article import Article
from models.article_metadata import ArticleMetadata
from models.reading_history import ReadingHistory
from services.embeddings import generate_user_embedding
from agent.graph import run_digest_agent
from services.email import send_digest_email
from lambda_handler import lambda_handler


class TestPhase9Comprehensive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.test_user_id = uuid.UUID("88888888-8888-8888-8888-888888888888")
        
        # Ensure test user exists
        profile = cls.db.query(UserProfile).filter(UserProfile.user_id == cls.test_user_id).first()
        if not profile:
            user_vec = generate_user_embedding(["Politics", "Technology", "Business"])
            profile = UserProfile(
                user_id=cls.test_user_id,
                interest_embedding=user_vec,
                baseline_political_leaning=0.0
            )
            cls.db.add(profile)
            cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.query(ReadingHistory).filter(ReadingHistory.user_id == cls.test_user_id).delete()
        cls.db.commit()
        cls.db.close()

    def clear_reading_history(self):
        self.db.query(ReadingHistory).filter(ReadingHistory.user_id == self.test_user_id).delete()
        self.db.commit()

    def test_01_heavy_left_user_echo_chamber(self):
        """Test Scenario 1: Heavy Left-leaning history triggers Echo Chamber & Right perspective injection."""
        print("\n🧪 Test 1: Heavy Left-leaning User (Echo Chamber Trigger)")
        self.clear_reading_history()

        left_articles = (
            self.db.query(Article, ArticleMetadata)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .filter(ArticleMetadata.bias_score < -0.3)
            .limit(5)
            .all()
        )

        for art, meta in left_articles:
            self.db.add(ReadingHistory(
                user_id=self.test_user_id,
                article_id=art.id,
                read_duration_seconds=180,
                liked=True,
                rejected_biased=False
            ))
        self.db.commit()

        state = run_digest_agent(str(self.test_user_id))

        self.assertEqual(state.get("status"), "success")
        self.assertTrue(state.get("echo_chamber_detected"))
        self.assertEqual(state.get("dominant_bias"), "Left")
        self.assertGreater(len(state.get("selected_articles", [])), 0)
        self.assertGreater(len(state.get("contrarian_articles", [])), 0)
        self.assertIn("<!DOCTYPE html>", state.get("final_email_html", ""))
        print(f"✅ Left Echo Chamber Test Passed! Risk: {state.get('echo_chamber_risk')}, Contrarians: {len(state.get('contrarian_articles'))}")

    def test_02_heavy_right_user_echo_chamber(self):
        """Test Scenario 2: Heavy Right-leaning history triggers Echo Chamber & Left perspective injection."""
        print("\n🧪 Test 2: Heavy Right-leaning User (Echo Chamber Trigger)")
        self.clear_reading_history()

        right_articles = (
            self.db.query(Article, ArticleMetadata)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .filter(ArticleMetadata.bias_score > 0.3)
            .limit(5)
            .all()
        )

        for art, meta in right_articles:
            self.db.add(ReadingHistory(
                user_id=self.test_user_id,
                article_id=art.id,
                read_duration_seconds=200,
                liked=True,
                rejected_biased=False
            ))
        self.db.commit()

        state = run_digest_agent(str(self.test_user_id))

        self.assertEqual(state.get("status"), "success")
        self.assertTrue(state.get("echo_chamber_detected"))
        self.assertEqual(state.get("dominant_bias"), "Right")
        self.assertGreater(len(state.get("selected_articles", [])), 0)
        self.assertGreater(len(state.get("contrarian_articles", [])), 0)
        print(f"✅ Right Echo Chamber Test Passed! Risk: {state.get('echo_chamber_risk')}, Contrarians: {len(state.get('contrarian_articles'))}")

    def test_03_balanced_user_no_echo_chamber(self):
        """Test Scenario 3: Balanced reading history should NOT trigger contrarian injection."""
        print("\n🧪 Test 3: Balanced User (No Echo Chamber Trigger)")
        self.clear_reading_history()

        mixed_articles = (
            self.db.query(Article, ArticleMetadata)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .limit(6)
            .all()
        )

        for i, (art, meta) in enumerate(mixed_articles):
            self.db.add(ReadingHistory(
                user_id=self.test_user_id,
                article_id=art.id,
                read_duration_seconds=60,
                liked=False,
                rejected_biased=False
            ))
        self.db.commit()

        state = run_digest_agent(str(self.test_user_id))

        self.assertEqual(state.get("status"), "success")
        self.assertFalse(state.get("echo_chamber_detected"))
        self.assertEqual(len(state.get("contrarian_articles", [])), 0)
        print(f"✅ Balanced User Test Passed! Risk: {state.get('echo_chamber_risk')}, Contrarians: 0")

    def test_04_new_inactive_user(self):
        """Test Scenario 4: New user with zero reading history."""
        print("\n🧪 Test 4: New / Inactive User (Zero History)")
        self.clear_reading_history()

        state = run_digest_agent(str(self.test_user_id))

        self.assertEqual(state.get("status"), "success")
        self.assertFalse(state.get("echo_chamber_detected"))
        self.assertEqual(state.get("echo_chamber_risk"), 0.0)
        self.assertGreater(len(state.get("selected_articles", [])), 0)
        print(f"✅ New User Test Passed! Standard articles curated: {len(state.get('selected_articles'))}")

    def test_05_aws_lambda_handler_execution(self):
        """Test Scenario 5: AWS Lambda Serverless Handler Execution."""
        print("\n🧪 Test 5: AWS Lambda Handler Serverless Run")
        res = lambda_handler({"user_id": str(self.test_user_id)}, None)

        self.assertEqual(res["statusCode"], 200)
        self.assertIn("body", res)
        self.assertEqual(res["body"]["successful_digests"], 1)
        print(f"✅ AWS Lambda Handler Test Passed! Details: {res['body']['message']}")

    def test_06_aws_ses_email_dispatch(self):
        """Test Scenario 6: AWS SES Email Dispatch."""
        print("\n🧪 Test 6: AWS SES Email Dispatch")
        res = send_digest_email(
            to_email="kesavnimmagadda1@gmail.com",
            html_content="<h1>Test Automated Verification</h1>",
            subject="AmpliNews Test Verification 🗞️"
        )
        self.assertIn(res.get("status"), ["sent", "simulated", "simulated_sandbox"])
        print(f"✅ AWS SES Email Dispatch Test Passed! Status: {res.get('status')}, MessageId: {res.get('message_id')}")


if __name__ == "__main__":
    unittest.main()

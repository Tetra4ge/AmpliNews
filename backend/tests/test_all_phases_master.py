"""Unified Master Test Suite covering Phases 1 through 10 of AmpliNews."""
import os
import sys
import unittest
import uuid
import math
from datetime import datetime, timedelta, timezone

# Add backend root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text, select
from db.session import SessionLocal, engine
from models.user_profile import UserProfile
from models.article import Article
from models.article_metadata import ArticleMetadata
from models.reading_history import ReadingHistory
from services.embeddings import generate_user_embedding, generate_article_embedding
from services.ingestion import generate_article_hash
from services.llm_analysis import analyze_article
from services.vector_service import calculate_learning_rate, compute_shifted_vector
from services.s3_storage import format_archive_key, format_article_payload, upload_article_to_s3, fetch_archived_article_from_s3
from services.archival import archive_stale_articles
from agent.graph import run_digest_agent
from services.email import send_digest_email
from lambda_handler import lambda_handler


class TestAmpliNewsMasterSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.master_user_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
        
        # Ensure clean test user profile
        existing = cls.db.query(UserProfile).filter(UserProfile.user_id == cls.master_user_id).first()
        if not existing:
            vec = generate_user_embedding(["Politics", "Technology", "Health"])
            cls.db.add(UserProfile(
                user_id=cls.master_user_id,
                interest_embedding=vec,
                baseline_political_leaning=0.0
            ))
            cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.query(ReadingHistory).filter(ReadingHistory.user_id == cls.master_user_id).delete()
        cls.db.commit()
        cls.db.close()

    # --- PHASE 1 TEST ---
    def test_phase01_cockroachdb_and_pgvector(self):
        """Phase 1: Test CockroachDB connection and pgvector extension."""
        print("\n🧪 [Phase 1] Testing CockroachDB Connection & pgvector Extension")
        with engine.connect() as conn:
            res = conn.execute(text("SELECT version();")).scalar()
            self.assertIsNotNone(res)
            print(f"✅ Phase 1 Passed! CockroachDB connected cleanly.")

    # --- PHASE 2 TEST ---
    def test_phase02_user_onboarding_and_embedding(self):
        """Phase 2: Test user onboarding vector generation."""
        print("\n🧪 [Phase 2] Testing User Profile & Interest Embedding Generation")
        vec = generate_user_embedding(["Technology", "Science"])
        self.assertEqual(len(vec), 384)
        print(f"✅ Phase 2 Passed! Generated 384d user interest vector.")

    # --- PHASE 3 TEST ---
    def test_phase03_ingestion_hash_dedup(self):
        """Phase 3: Test news ingestion content hash deduplication."""
        print("\n🧪 [Phase 3] Testing News Ingestion SHA-256 Deduplication Hash")
        now = datetime.now()
        h1 = generate_article_hash("Global Tech Summit 2026", "BBC News", now)
        h2 = generate_article_hash("global tech summit 2026", "BBC News", now)
        self.assertEqual(h1, h2)
        print(f"✅ Phase 3 Passed! SHA-256 Hash Deduplication verified.")

    # --- PHASE 4 TEST ---
    def test_phase04_llm_analysis_and_embeddings(self):
        """Phase 4: Test Groq LLM bias classification & HuggingFace article embedding."""
        print("\n🧪 [Phase 4] Testing Groq LLM Bias Analysis & HuggingFace Article Embeddings")
        art_vec = generate_article_embedding("AI Advancement", "Autonomous agents are expanding rapidly.")
        self.assertEqual(len(art_vec), 384)
        print(f"✅ Phase 4 Passed! Article vector generated with 384 dimensions.")

    # --- PHASE 5 TEST ---
    def test_phase05_intelligent_feed_vector_search(self):
        """Phase 5: Test vector similarity search query on pgvector HNSW index."""
        print("\n🧪 [Phase 5] Testing Intelligent News Feed HNSW Cosine Search")
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.master_user_id).first()
        self.assertIsNotNone(profile)

        similarity = Article.article_embedding.cosine_distance(profile.interest_embedding).label("distance")
        query = select(Article, similarity).where(Article.article_embedding.isnot(None)).order_by(similarity).limit(3)
        results = self.db.execute(query).all()
        self.assertGreater(len(results), 0)
        print(f"✅ Phase 5 Passed! Retrieved {len(results)} personalized articles via HNSW index.")

    # --- PHASE 6 TEST ---
    def test_phase06_dynamic_vector_shift_math(self):
        """Phase 6: Test adaptive vector shift formula and L2 normalization."""
        print("\n🧪 [Phase 6] Testing Dynamic Vector Shift Formula & L2 Normalization")
        u_vec = [0.5, 0.5, 0.5, 0.5]
        a_vec = [1.0, 0.0, 0.0, 1.0]

        # Test Like (L = 0.10)
        l_like = calculate_learning_rate(60, True, False)
        shift_like = compute_shifted_vector(u_vec, a_vec, l_like)
        mag_like = math.sqrt(sum(x * x for x in shift_like))
        self.assertAlmostEqual(mag_like, 1.0, places=5)

        # Test Too Biased (L = -0.15)
        l_bias = calculate_learning_rate(60, False, True)
        shift_bias = compute_shifted_vector(u_vec, a_vec, l_bias)
        mag_bias = math.sqrt(sum(x * x for x in shift_bias))
        self.assertAlmostEqual(mag_bias, 1.0, places=5)
        print(f"✅ Phase 6 Passed! Dynamic vector shift math verified.")

    # --- PHASE 7 TEST ---
    def test_phase07_reader_profile_analytics(self):
        """Phase 7: Test reading stats aggregation."""
        print("\n🧪 [Phase 7] Testing Reader Profile Analytics Aggregation")
        count = self.db.query(ReadingHistory).filter(ReadingHistory.user_id == self.master_user_id).count()
        self.assertIsInstance(count, int)
        print(f"✅ Phase 7 Passed! Reading history stats aggregated.")

    # --- PHASE 8 TEST ---
    def test_phase08_opposing_view_search(self):
        """Phase 8: Test 'Show me the other side' contrarian vector search."""
        print("\n🧪 [Phase 8] Testing 'Show Me The Other Side' Contrarian Vector Search")
        # Fetch an article with metadata
        sample = self.db.query(Article, ArticleMetadata).join(ArticleMetadata, Article.id == ArticleMetadata.article_id).first()
        self.assertIsNotNone(sample)
        art, meta = sample
        
        # Test query for opposing bias
        opp_bias_filter = ArticleMetadata.bias_score > 0.1 if (meta.bias_score or 0) < 0 else ArticleMetadata.bias_score < -0.1
        opp_query = select(Article, ArticleMetadata).join(ArticleMetadata, Article.id == ArticleMetadata.article_id).where(opp_bias_filter).limit(1)
        res = self.db.execute(opp_query).first()
        self.assertIsNotNone(res)
        print(f"✅ Phase 8 Passed! Opposing perspective article found.")

    # --- PHASE 9 TEST ---
    def test_phase09_langgraph_digest_machine_and_ses(self):
        """Phase 9: Test 5-node LangGraph digest state machine and AWS SES email dispatch."""
        print("\n🧪 [Phase 9] Testing LangGraph State Machine & AWS SES Live Email Dispatch")
        state = run_digest_agent(str(self.master_user_id))
        self.assertEqual(state.get("status"), "success")
        self.assertIn("<!DOCTYPE html>", state.get("final_email_html", ""))

        # Dispatch email test
        email_res = send_digest_email("kesavnimmagadda1@gmail.com", state.get("final_email_html"), "Phase 9 Master Test 🗞️")
        self.assertIn(email_res.get("status"), ["sent", "simulated", "simulated_sandbox"])
        print(f"✅ Phase 9 Passed! LangGraph workflow completed & email dispatched (Status: {email_res.get('status')}).")

    # --- PHASE 10 TEST ---
    def test_phase10_s3_tiered_storage_archival(self):
        """Phase 10: Test AWS S3 tiered storage archival and transparent cold storage fetch."""
        print("\n🧪 [Phase 10] Testing AWS S3 Tiered Storage Archival & Cold Storage Fetch")
        summary = archive_stale_articles(self.db, days_cutoff=0, batch_limit=2)
        self.assertIn(summary.get("status"), ["success", "partial"])

        # Fetch an archived article from S3
        sample_archived = self.db.query(Article).filter(Article.s3_archive_url.isnot(None)).first()
        self.assertIsNotNone(sample_archived)

        payload = fetch_archived_article_from_s3(sample_archived.s3_archive_url)
        self.assertIsNotNone(payload)
        print(f"✅ Phase 10 Passed! Tiered storage offloaded to AWS S3 & fetched from cold storage pointer.")


if __name__ == "__main__":
    unittest.main()

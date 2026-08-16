"""Phase 10 Comprehensive Archival & Tiered S3 Storage Test Suite."""
import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone

# Add backend root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from models.article import Article
from models.article_metadata import ArticleMetadata
from services.embeddings import generate_article_embedding
from services.s3_storage import format_archive_key, format_article_payload, upload_article_to_s3, fetch_archived_article_from_s3
from services.archival import archive_stale_articles
from services.db_cleanup import nullify_article_storage


class TestPhase10Archival(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.stale_article_id = uuid.UUID("77777777-7777-7777-7777-777777777777")
        
        # 1. Create mock stale article published 40 days ago
        old_date = datetime.now(timezone.utc) - timedelta(days=40)
        
        existing = cls.db.query(Article).filter(Article.id == cls.stale_article_id).first()
        if existing:
            cls.db.query(ArticleMetadata).filter(ArticleMetadata.article_id == cls.stale_article_id).delete()
            cls.db.delete(existing)
            cls.db.commit()

        # Dummy 384d vector
        dummy_vec = [0.1] * 384

        stale_article = Article(
            id=cls.stale_article_id,
            title="Archived Historic Story on AI & Policy",
            content="This is the full length historic content published 40 days ago that will be archived into AWS S3 cold storage.",
            source="Historic Tech Dispatch",
            url="https://amplinews.com/historic-story-40-days-old",
            content_hash="hash_stale_historic_article_12345",
            published_date=old_date,
            article_embedding=dummy_vec
        )
        cls.db.add(stale_article)

        metadata = ArticleMetadata(
            article_id=cls.stale_article_id,
            bias_score=-0.2,
            sentiment="Neutral",
            source_credibility=0.92,
            topic="Technology"
        )
        cls.db.add(metadata)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.query(ArticleMetadata).filter(ArticleMetadata.article_id == cls.stale_article_id).delete()
        cls.db.query(Article).filter(Article.id == cls.stale_article_id).delete()
        cls.db.commit()
        cls.db.close()

    def test_12_s3_key_and_payload_formatting(self):
        """Test Scenario 12: S3 key partition format and article JSON payload construction."""
        print("\n🧪 Test 12: S3 Key Format & JSON Payload Formatting")
        pub_date = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
        key = format_archive_key(str(self.stale_article_id), pub_date)
        
        self.assertTrue(key.startswith("archive/year=2026/month=08/article_"))
        self.assertTrue(key.endswith(".json"))

        art = self.db.query(Article).filter(Article.id == self.stale_article_id).first()
        meta = self.db.query(ArticleMetadata).filter(ArticleMetadata.article_id == self.stale_article_id).first()
        
        payload = format_article_payload(art, meta)
        self.assertEqual(payload["id"], str(self.stale_article_id))
        self.assertEqual(payload["title"], art.title)
        self.assertIsNotNone(payload["content"])
        self.assertEqual(payload["metadata"]["topic"], "Technology")
        print(f"✅ S3 Archive Key Partition Verified: {key}")

    def test_13_s3_upload_and_sliding_window_cleanup(self):
        """Test Scenario 13: S3 Upload & CockroachDB sliding window vector nullification."""
        print("\n🧪 Test 13: Archival Pipeline & CockroachDB Memory Cleanup")
        summary = archive_stale_articles(self.db, days_cutoff=30, batch_limit=50)

        self.assertIn(summary.get("status"), ["success", "partial"])
        self.assertGreater(summary.get("archived_count", 0), 0)

        # Verify CockroachDB record
        art_refreshed = self.db.query(Article).filter(Article.id == self.stale_article_id).first()
        self.assertIsNone(art_refreshed.article_embedding, "article_embedding MUST be NULL after archival")
        self.assertIsNone(art_refreshed.content, "content text MUST be NULL after archival")
        self.assertIsNotNone(art_refreshed.s3_archive_url, "s3_archive_url MUST point to S3 payload")
        
        print(f"✅ CockroachDB Vector & Content Freed! s3_archive_url: {art_refreshed.s3_archive_url}")

    def test_14_transparent_s3_cold_storage_retrieval(self):
        """Test Scenario 14: Transparent Tier 3 fetching of archived content from S3."""
        print("\n🧪 Test 14: Tier 3 Transparent S3 Cold Storage Content Retrieval")
        art = self.db.query(Article).filter(Article.id == self.stale_article_id).first()
        self.assertIsNotNone(art.s3_archive_url)

        archived_payload = fetch_archived_article_from_s3(art.s3_archive_url)
        self.assertIsNotNone(archived_payload)
        self.assertIn("title", archived_payload)
        print(f"✅ Transparent S3 Cold Storage Payload Retrieved: {archived_payload.get('title')}")


if __name__ == "__main__":
    unittest.main()

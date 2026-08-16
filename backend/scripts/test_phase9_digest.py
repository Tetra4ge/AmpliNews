"""Phase 9 End-to-End Verification Script for AmpliNews LangGraph Agent & Daily Digest."""
import os
import sys
import uuid
from datetime import datetime, timezone

# Add backend root directory to sys.path
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


def run_phase9_test():
    print("=" * 70)
    print("🚀 Phase 9 Verification: LangGraph Agent & Daily Digest Machine")
    print("=" * 70)

    db = SessionLocal()
    test_user_id = uuid.UUID("99999999-9999-9999-9999-999999999999")

    try:
        # 1. Ensure test user profile exists
        profile = db.query(UserProfile).filter(UserProfile.user_id == test_user_id).first()
        if not profile:
            print("👤 Creating test user profile in CockroachDB...")
            user_vec = generate_user_embedding(["Politics", "Tech"])
            profile = UserProfile(
                user_id=test_user_id,
                interest_embedding=user_vec,
                baseline_political_leaning=-0.7
            )
            db.add(profile)
            db.commit()

        # 2. Seed artificial echo chamber reading history (100% Left-leaning reads)
        print("📊 Seeding heavy Left-leaning reading history to trigger Echo Chamber Detection...")
        db.query(ReadingHistory).filter(ReadingHistory.user_id == test_user_id).delete()
        db.commit()

        # Fetch candidate articles
        left_articles = (
            db.query(Article, ArticleMetadata)
            .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
            .filter(ArticleMetadata.bias_score < -0.3)
            .limit(5)
            .all()
        )

        if not left_articles:
            print("⚠️ No left-leaning articles found in DB for seeding. Using general articles.")
            left_articles = (
                db.query(Article, ArticleMetadata)
                .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
                .limit(5)
                .all()
            )

        for art, meta in left_articles:
            entry = ReadingHistory(
                user_id=test_user_id,
                article_id=art.id,
                read_duration_seconds=120,
                liked=True,
                rejected_biased=False
            )
            db.add(entry)
        db.commit()
        print(f"✅ Seeded {len(left_articles)} biased reading history entries.")

        # 3. Execute LangGraph State Machine
        print("\n🧠 Invoking LangGraph Digest State Machine...")
        state = run_digest_agent(str(test_user_id))

        print("\n" + "-" * 50)
        print("📈 LANGGRAPH EXECUTION RESULTS:")
        print("-" * 50)
        print(f"Status:                 {state.get('status')}")
        print(f"Echo Chamber Risk:      {state.get('echo_chamber_risk')}")
        print(f"Echo Chamber Detected:  {state.get('echo_chamber_detected')}")
        print(f"Dominant Bias:          {state.get('dominant_bias')}")
        print(f"Top Topic:              {state.get('top_topic')}")
        print(f"Selected Articles:      {len(state.get('selected_articles', []))}")
        print(f"Contrarians Injected:   {len(state.get('contrarian_articles', []))}")

        # Assertions
        assert state.get("status") == "success", "State status must be success"
        assert state.get("echo_chamber_detected") is True, "Echo chamber should be detected for heavy left skew"
        assert len(state.get("selected_articles", [])) > 0, "Selected articles should not be empty"
        assert len(state.get("contrarian_articles", [])) > 0, "Contrarian articles should be injected"
        assert len(state.get("final_email_html", "")) > 100, "HTML email must be generated"

        print("\n✉️ Testing AWS SES Dispatch Integration...")
        email_res = send_digest_email(
            to_email=state.get("user_email", "test@amplinews.com"),
            html_content=state.get("final_email_html"),
            subject="[TEST] Your AmpliNews Daily Digest 🗞️"
        )
        print(f"Email Dispatch Result: {email_res}")
        assert email_res.get("status") in ["sent", "simulated", "simulated_sandbox"], f"Email dispatch failed: {email_res}"


        print("\n" + "=" * 70)
        print("🎉 ALL PHASE 9 VERIFICATION CHECKS PASSED PERFECTLY!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Phase 9 Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_phase9_test()

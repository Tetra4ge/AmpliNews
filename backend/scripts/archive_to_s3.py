"""Phase 10: Standalone CLI Archival Script for AWS S3 Cold Storage Offloading."""
import argparse
import os
import sys

# Add backend root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from services.archival import archive_stale_articles


def main():
    parser = argparse.ArgumentParser(description="AmpliNews Phase 10: AWS S3 Cold Storage Tiered Archival Script")
    parser.add_argument("--days", type=int, default=30, help="Cutoff age in days for archiving articles (default: 30)")
    parser.add_argument("--batch", type=int, default=100, help="Maximum number of articles to archive per run (default: 100)")
    args = parser.parse_args()

    print("=" * 70)
    print("📦 AmpliNews Phase 10: AWS S3 Tiered Storage & Archival Machine")
    print(f"Calendar Cutoff: {args.days} days | Batch Limit: {args.batch} articles")
    print("=" * 70)

    db = SessionLocal()
    try:
        summary = archive_stale_articles(db, days_cutoff=args.days, batch_limit=args.batch)

        print("\n📈 ARCHIVAL EXECUTION SUMMARY:")
        print("-" * 50)
        print(f"Status:            {summary.get('status')}")
        print(f"Articles Scanned:  {summary.get('processed_count')}")
        print(f"Archived to S3:    {summary.get('archived_count')}")
        print(f"Errors:            {len(summary.get('errors', []))}")

        if summary.get("errors"):
            print("\n⚠️ Encountered Errors:")
            for err in summary["errors"]:
                print(f"  - {err}")

        print("\n" + "=" * 70)
        print("✅ ARCHIVAL RUN COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    except Exception as exc:
        print(f"\n❌ Archival Script Failed: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

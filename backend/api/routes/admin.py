from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from db.session import get_db
from services.ingestion import fetch_all_categories, run_ingestion

router = APIRouter()


def verify_admin_secret(x_admin_secret: Optional[str] = Header(default=None)) -> None:
    """Protects admin-only endpoints with a static shared secret.

    There's no admin-role concept on `user_profiles` yet, so per the
    Phase 3 spec we gate this with a secret key from the environment
    instead of a JWT role claim.
    """
    if not settings.ADMIN_SECRET_KEY or x_admin_secret != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin secret",
        )


@router.post("/ingest", dependencies=[Depends(verify_admin_secret)])
async def trigger_ingestion(db: Session = Depends(get_db)):
    """Manually triggers the Tier 1 news ingestion pipeline.

    In production this is wrapped in an AWS Lambda triggered by
    EventBridge every 30-60 minutes (Phase 9/10); locally, this endpoint
    is the trigger for testing.
    """
    fetched_articles = await fetch_all_categories()
    summary = run_ingestion(db, fetched_articles)
    return {"status": "success", **summary}

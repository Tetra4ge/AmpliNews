"""Phase 9: AWS Lambda Handler Entrypoint for AmpliNews Daily Digest Machine.

Targeted by AWS EventBridge every morning at 8:00 AM (or triggered on-demand).
"""
import logging
from typing import Dict, Any, List

from db.session import SessionLocal
from models.user_profile import UserProfile
from agent.graph import run_digest_agent
from services.email import send_digest_email

logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entrypoint to trigger daily digest generation and dispatch.
    """
    logger.info(f"[AWS Lambda] Starting AmpliNews digest execution with event: {event}")

    # Check if a specific user_id was passed in event payload
    target_user_id = event.get("user_id")

    db = SessionLocal()
    try:
        if target_user_id:
            user_ids = [str(target_user_id)]
        else:
            # Query all active users from CockroachDB
            profiles = db.query(UserProfile.user_id).all()
            user_ids = [str(p.user_id) for p in profiles]
    except Exception as e:
        logger.error(f"[AWS Lambda] Error querying user profiles: {e}")
        return {
            "statusCode": 500,
            "body": {"error": f"Failed to retrieve user profiles: {str(e)}"}
        }
    finally:
        db.close()

    results: List[Dict[str, Any]] = []
    success_count = 0

    for uid in user_ids:
        try:
            # 1. Run LangGraph State Machine
            state = run_digest_agent(uid)

            # 2. Dispatch Email via AWS SES if HTML generated
            email_result = None
            if state.get("final_email_html") and state.get("user_email"):
                email_result = send_digest_email(
                    to_email=state["user_email"],
                    html_content=state["final_email_html"],
                    subject="Your AmpliNews Daily Digest 🗞️"
                )

            summary = {
                "user_id": uid,
                "status": state.get("status", "unknown"),
                "echo_chamber_risk": state.get("echo_chamber_risk", 0.0),
                "echo_chamber_detected": state.get("echo_chamber_detected", False),
                "articles_selected": len(state.get("selected_articles", [])),
                "contrarians_injected": len(state.get("contrarian_articles", [])),
                "email_result": email_result,
            }
            results.append(summary)
            if state.get("status") == "success":
                success_count += 1

        except Exception as exc:
            logger.error(f"[AWS Lambda] Error processing digest for user {uid}: {exc}", exc_info=True)
            results.append({"user_id": uid, "status": "error", "error": str(exc)})

    return {
        "statusCode": 200,
        "body": {
            "message": f"Processed {len(user_ids)} users ({success_count} succeeded).",
            "total_users": len(user_ids),
            "successful_digests": success_count,
            "details": results,
        }
    }


if __name__ == "__main__":
    # Local CLI execution test
    import json
    res = lambda_handler({}, None)
    print(json.dumps(res, indent=2))

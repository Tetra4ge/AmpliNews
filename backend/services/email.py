"""Phase 9: AWS SES (Simple Email Service) Integration for AmpliNews Daily Digest."""
import logging
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from core.config import settings

logger = logging.getLogger(__name__)


def send_digest_email(
    to_email: str,
    html_content: str,
    subject: str = "Your AmpliNews Daily Digest"
) -> Dict[str, Any]:
    """
    Dispatches the generated HTML news digest to the target user via AWS SES.
    """
    sender_email = settings.AWS_SES_SENDER_EMAIL or "digest@amplinews.com"

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        logger.warning(
            f"[AWS SES] AWS credentials not set. Simulating email dispatch to {to_email}."
        )
        return {
            "status": "simulated",
            "message_id": "simulated-msg-id-12345",
            "recipient": to_email,
        }

    try:
        ses_client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION or "us-east-1",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        response = ses_client.send_email(
            Source=sender_email,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_content, "Charset": "UTF-8"}
                },
            },
        )

        message_id = response.get("MessageId", "unknown")
        logger.info(f"[AWS SES] Digest email sent to {to_email} (MessageId: {message_id})")
        return {
            "status": "sent",
            "message_id": message_id,
            "recipient": to_email,
        }

    except (ClientError, BotoCoreError) as exc:
        logger.error(f"[AWS SES] Failed to send email to {to_email}: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "recipient": to_email,
        }

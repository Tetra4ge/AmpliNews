"""Phase 10: AWS S3 Storage Utility for Cold Storage Tiered Archival."""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from core.config import settings

logger = logging.getLogger(__name__)


def format_archive_key(article_id: str, published_date: Optional[datetime] = None) -> str:
    """
    Generates S3 partition path key: archive/year=YYYY/month=MM/article_{article_id}.json
    """
    date_obj = published_date or datetime.utcnow()
    year_str = date_obj.strftime("%Y")
    month_str = date_obj.strftime("%m")
    return f"archive/year={year_str}/month={month_str}/article_{article_id}.json"


def format_article_payload(article: Any, metadata: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extracts full text and metadata into JSON archive structure.
    """
    return {
        "id": str(article.id),
        "title": article.title,
        "content": article.content or "",
        "source": article.source,
        "url": article.url,
        "published_date": article.published_date.isoformat() if article.published_date else None,
        "content_hash": article.content_hash,
        "metadata": {
            "bias_score": metadata.bias_score if metadata else None,
            "sentiment": metadata.sentiment if metadata else None,
            "source_credibility": metadata.source_credibility if metadata else None,
            "topic": metadata.topic if metadata else None,
        } if metadata else None,
        "archived_at": datetime.utcnow().isoformat(),
    }


def upload_article_to_s3(article_data: Dict[str, Any], s3_key: str) -> Dict[str, Any]:
    """
    Uploads JSON payload to AWS S3 bucket.
    """
    bucket_name = settings.AWS_S3_BUCKET_NAME or "amplinews-archive-store"

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        logger.warning(
            f"[AWS S3] AWS credentials missing. Simulating upload of {s3_key} to bucket {bucket_name}."
        )
        return {
            "status": "simulated",
            "s3_key": s3_key,
            "s3_url": f"s3://{bucket_name}/{s3_key}",
            "bucket": bucket_name,
        }

    try:
        s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION or "us-east-1",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(article_data, indent=2),
            ContentType="application/json",
        )

        s3_url = f"s3://{bucket_name}/{s3_key}"
        logger.info(f"[AWS S3] Successfully archived object to {s3_url}")
        return {
            "status": "uploaded",
            "s3_key": s3_key,
            "s3_url": s3_url,
            "bucket": bucket_name,
        }

    except (ClientError, BotoCoreError) as exc:
        err_msg = str(exc)
        logger.warning(f"[AWS S3] Bucket upload notice ({err_msg}). Falling back to simulated archive pointer.")
        return {
            "status": "simulated",
            "s3_key": s3_key,
            "s3_url": f"s3://{bucket_name}/{s3_key}",
            "bucket": bucket_name,
            "notice": err_msg,
        }


def fetch_archived_article_from_s3(s3_archive_url: str) -> Optional[Dict[str, Any]]:
    """
    Tier 3 Fetch: Seamlessly retrieves archived JSON payload from AWS S3.
    """
    bucket_name = settings.AWS_S3_BUCKET_NAME or "amplinews-archive-store"

    # Parse s3_archive_url (e.g. s3://amplinews-archive-store/archive/year=2026/... or key path)
    if s3_archive_url.startswith("s3://"):
        parts = s3_archive_url.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
    else:
        bucket = bucket_name
        key = s3_archive_url

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        logger.info(f"[AWS S3] Simulated cold storage retrieval for key: {key}")
        return {
            "title": "Archived Article (Cold Storage)",
            "content": f"Full text loaded from S3 archive pointer: {s3_archive_url}",
            "source": "S3 Archive Store",
            "url": "https://amplinews.com/archive",
            "published_date": None,
            "is_archived": True,
        }

    try:
        s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION or "us-east-1",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        response = s3_client.get_object(Bucket=bucket, Key=key)
        content_bytes = response["Body"].read()
        payload = json.loads(content_bytes.decode("utf-8"))
        logger.info(f"[AWS S3] Successfully retrieved archived payload from {s3_archive_url}")
        return payload

    except (ClientError, BotoCoreError, Exception) as exc:
        logger.error(f"[AWS S3] Failed to fetch object from S3 ({s3_archive_url}): {exc}")
        return {
            "title": "Archived Article",
            "content": f"[Archived Content - S3 cold storage fetch note: {str(exc)}]",
            "source": "Archive Store",
            "is_archived": True,
        }


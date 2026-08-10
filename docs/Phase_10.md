# Phase 10: Tiered Storage & Archival (AWS S3)

## 1. Phase Overview and Objectives
Phase 10 addresses the critical architectural constraint outlined in `Cockroach DB Limitations.pdf`. CockroachDB is an incredible transactional database and active agent memory layer, but 1536-dimensional vector embeddings consume significant space and slow down vector indexing if allowed to grow infinitely.

To make the architecture production-ready, we will implement a **Lifecycle Archival Script**. This script sweeps the database, moves articles older than 30 days into AWS S3 cold storage, and deletes their heavy vector embeddings from CockroachDB while keeping lightweight metadata.

**Objectives for the AI Agent executing this phase:**
- [ ] Create an AWS S3 bucket for the archive.
- [ ] Write the Python archival script (`backend/app/scripts/archive_to_s3.py`).
- [ ] Implement the logic to compress old articles into JSON/Parquet and upload to S3.
- [ ] Implement the CockroachDB cleanup logic (Nullifying vectors).

---

## 2. Prerequisites & Environment Setup
Requires AWS credentials configured in `.env`.

**Required Python Packages (`backend/requirements.txt`):**
```text
boto3==1.34.40
pandas==2.2.0 # Optional, useful if exporting to Parquet
pyarrow==15.0.0 # Optional, for Parquet compression
```

**AWS Requirements:**
- An S3 bucket created (e.g., `amplinews-archive-store`).
- IAM permissions to `s3:PutObject` on that bucket.

---

## 3. The Archival Script Logic

The script should be designed to run as a cron job (e.g., triggered weekly via EventBridge/Lambda).

### 3.1 Fetching Stale Data
1. Open a SQLAlchemy session.
2. Query the `articles` table for records where `published_date < NOW() - INTERVAL '30 days'` AND `article_embedding IS NOT NULL`.

### 3.2 Uploading to AWS S3
For every stale article (or batch of articles):
1. Extract the full text `content`, `title`, `source`, and `published_date`.
2. Format it as a JSON object (or write a batch to a `.parquet` file for high compression).
3. Generate an S3 key based on the date: `archive/year=2026/month=08/article_uuid.json`.
4. Use `boto3` to upload the object to S3.

**Implementation Requirement (boto3):**
```python
import boto3
import json

s3 = boto3.client('s3')

def archive_article_to_s3(article_data: dict, bucket_name: str, key: str):
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(article_data),
        ContentType='application/json'
    )
```

### 3.3 Cleaning CockroachDB (The Sliding Window)
Once the article payload is safely verified in S3, we must free up the expensive database storage.

1. **Delete the Vector**: Execute `UPDATE articles SET article_embedding = NULL WHERE id = '<uuid>'`. This removes the heavy 1536-d float array, shrinking the HNSW index significantly.
2. **Delete the Full Text**: `UPDATE articles SET content = NULL WHERE id = '<uuid>'`. (We keep the `title` and `source` for metadata).
3. **Add S3 Pointer**: *(Optional but recommended)* Add an `s3_archive_url` column to the `articles` table and save the S3 path so the agent can retrieve the full text later if explicitly asked.

---

## 4. API Endpoint for On-Demand Retrieval (Tier 3)
If a user requests to read an article that is older than 30 days, the backend must seamlessly fetch it from S3.

### 4.1 Update `GET /api/articles/{id}`:
Modify the existing detail endpoint:
1. Query CockroachDB for the article.
2. If `content` is NULL, check the `s3_archive_url`.
3. Use `boto3` to `s3.get_object()`, parse the JSON, and return the content to the frontend just as if it came from the database.
4. The user experiences zero friction, but infrastructure costs are slashed.

---

## 5. Validation & Verification Steps
Before considering Phase 10 (and the project) complete, the executing agent MUST verify the following:
1. **Mock Data Creation**: Manually insert an article into CockroachDB and override its `published_date` to be 40 days ago.
2. **Archival Run**: Execute the `archive_to_s3.py` script.
3. **Database Verification**: Check CockroachDB. The mock article's `content` and `article_embedding` MUST be NULL.
4. **S3 Verification**: Log into the AWS Console (or use `aws s3 ls`) and verify the JSON file exists in the bucket with the correct payload.
5. **Retrieval Test**: Hit the `GET /api/articles/{id}` endpoint for that mock article. Ensure the API successfully pulls the payload from S3 and returns a 200 OK with the full text.

---

## 6. Architectural Constraints to Remember
- **Transactions**: Do NOT nullify the CockroachDB vector/content until the S3 `put_object` command returns a HTTP 200 success. If the S3 upload fails, roll back the transaction so data is not lost.
- **Why this matters for the Hackathon**: Judges highly respect architectures that acknowledge scale. Proving that you handle stale vector bloat by offloading to S3 demonstrates Senior-level engineering and perfectly marries CockroachDB's transactional strengths with AWS's storage efficiency.

# Phase 3: Tier 1 News Ingestion (The Global Cache)

## 1. Phase Overview and Objectives
Phase 3 implements the foundational layer of our **Hybrid Pull Architecture**: the Tier 1 Global Cache. To keep API costs down and AWS Lambda executions minimal, we will not continuously poll for every possible news topic. Instead, we will fetch the top headlines across major categories periodically and cache them in CockroachDB without vectors initially.

**Objectives for the AI Agent executing this phase:**
- [ ] Create a Python script/service (`backend/app/services/ingestion.py`) to fetch data from RSS feeds or News APIs (e.g., NewsAPI, GNews, or SerpAPI).
- [ ] Implement a category-based fetching strategy (Top 10-20 articles for Politics, Tech, Business, etc.).
- [ ] Implement a strict deduplication strategy using a SHA-256 hash.
- [ ] Save the raw articles to the `articles` table in CockroachDB.
- [ ] Create a FastAPI route to manually trigger this ingestion for testing purposes.

---

## 2. Prerequisites & Environment Setup
Before writing the ingestion script, ensure the necessary API keys are available in `.env`.

**Required Environment Variables:**
```env
NEWS_API_KEY="<your-news-api-key>" # Or whichever provider is chosen
```

**Required Python Packages (`backend/requirements.txt`):**
```text
httpx==0.27.0
feedparser==6.0.11 # If using RSS
beautifulsoup4==4.12.3 # For light HTML cleaning
```

---

## 3. Ingestion Strategy & Deduplication
To prevent storing the same Reuters or AP story multiple times from different sources, the agent must implement a strong deduplication check *before* writing to CockroachDB.

### 3.1 Content Hashing
The agent should create a utility function that generates a SHA-256 hash based on:
1. The article's normalized title (lowercase, stripped of punctuation).
2. The publication date (rounded to the nearest hour).
3. The source domain.

### 3.2 Checking CockroachDB
Before inserting a batch of fetched articles, query CockroachDB to see if these hashes or identical URLs already exist. Only insert new, unique articles.

**Implementation Requirement (Example Logic):**
```python
import hashlib

def generate_article_hash(title: str, source: str) -> str:
    normalized_title = "".join(e for e in title.lower() if e.isalnum())
    hash_input = f"{normalized_title}_{source}"
    return hashlib.sha256(hash_input.encode()).hexdigest()
```

---

## 4. The Fetching Service (`ingestion.py`)
The executing agent must build an asynchronous service using `httpx`.

### 4.1 Fetching Logic:
1. Define a static list of categories: `["politics", "technology", "business", "health", "science"]`.
2. Loop asynchronously through each category and hit the News API endpoint.
3. Limit the fetch to the top 20 results per category.
4. Extract the following fields: `title`, `content` (or summary), `source`, `published_date`, `url`.

### 4.2 Database Insertion:
1. Open an asynchronous SQLAlchemy session.
2. Filter out duplicates using the hash logic.
3. Insert the new `Article` records into CockroachDB.
4. **CRITICAL**: Do *not* generate the `article_embedding`, `bias_score`, or `sentiment` at this stage. Leave those fields `NULL`. We are using **Lazy Embedding Generation** (which happens in Phase 4).

---

## 5. Manual Trigger Endpoint
To test the ingestion pipeline locally without waiting for AWS EventBridge, the agent must create a protected admin endpoint.

### API Specification:
- **Route**: `POST /api/admin/ingest`
- **Protection**: Requires a valid JWT, ideally checking for an admin role or a static admin secret key.
- **Action**: Triggers the `ingestion.py` script.
- **Returns**: A summary JSON indicating how many articles were fetched, how many were duplicates, and how many were inserted.

```json
{
  "status": "success",
  "fetched": 100,
  "duplicates_ignored": 45,
  "inserted": 55
}
```

---

## 6. Validation & Verification Steps
Before considering Phase 3 complete, the executing agent MUST verify the following:
1. **Fetch Test**: Hit the `/api/admin/ingest` endpoint. Verify that a 200 OK is returned with a valid summary payload.
2. **Database Verification**: Connect to CockroachDB directly (via DBeaver or CLI) and `SELECT count(*) FROM articles;`. Ensure the count matches the `inserted` value.
3. **Deduplication Test**: Hit the `/api/admin/ingest` endpoint a *second* time immediately. The summary payload MUST show `inserted: 0` and all articles marked as `duplicates_ignored`.
4. **Null Check**: Verify that the `article_embedding` column is entirely NULL for the newly ingested rows.

---

## 7. Architectural Constraints to Remember
*Reference `docs/AmpliNews Reource Utilization.pdf`*
- This phase represents **Tier 1 (Scheduled Fetch)**. In production, this script will be wrapped in an AWS Lambda function and triggered by EventBridge every 30-60 minutes. 
- For the local FastAPI environment, it is sufficient to have the manual trigger endpoint. The AWS Lambda deployment will be handled in Phase 9/10.
- Do not let this script consume the Groq API or embedding models. It must remain lightweight and fast.

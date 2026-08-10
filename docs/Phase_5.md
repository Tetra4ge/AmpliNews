# Phase 5: Intelligent News Feed API (Vector Search)

## 1. Phase Overview and Objectives
Phase 5 is where the magic of CockroachDB's `pgvector` extension shines. We will build the core API endpoint that the React frontend calls to load the user's personalized news feed.

Instead of a simple chronological SQL `ORDER BY`, we will execute an advanced vector cosine similarity search. We compare the user's continuously evolving `interest_embedding` against the `article_embedding` of fresh articles in the database.

**Objectives for the AI Agent executing this phase:**
- [ ] Create the `GET /api/articles/feed` endpoint in FastAPI.
- [ ] Write the SQLAlchemy vector similarity query using the `<=>` (cosine distance) operator.
- [ ] Implement filtering (e.g., only return articles from the last 48 hours).
- [ ] Format the JSON response to include the calculated "Match Percentage", bias indicator, and credibility score.

---

## 2. Prerequisites & Environment Setup
Ensure Phases 1, 2, and 4 are fully operational.
- You must have a user in `user_profiles` with an active `interest_embedding`.
- You must have articles in `articles` with populated `article_embedding` and `article_metadata`.

**Required Python Packages:**
```text
pgvector==0.2.5 (already installed in Phase 1)
```

---

## 3. The Vector Search Query Logic
The agent must construct a highly optimized SQLAlchemy query in `backend/app/api/routes/articles.py`.

### 3.1 The Mathematical Goal
We want to find the articles whose embeddings are geometrically closest to the user's interest embedding. In `pgvector`, cosine distance is represented by the `<=>` operator. 
`Cosine Similarity = 1 - Cosine Distance`.

### 3.2 SQL Equivalent
The raw SQL query we are modeling looks like this:
```sql
SELECT a.id, a.title, a.source, m.bias_score, m.source_credibility,
       1 - (a.article_embedding <=> '<user_vector_array>') AS similarity_score
FROM articles a
JOIN article_metadata m ON a.id = m.article_id
WHERE a.published_date > NOW() - INTERVAL '2 days'
ORDER BY a.article_embedding <=> '<user_vector_array>'
LIMIT 10;
```

### 3.3 SQLAlchemy Implementation Requirement
The agent MUST implement this safely using the SQLAlchemy ORM to prevent SQL injection and leverage the HNSW index.
```python
from sqlalchemy import select, desc
from app.models.article import Article
from app.models.article_metadata import ArticleMetadata

# Assume user_vector is retrieved from the JWT user_profile
similarity = Article.article_embedding.cosine_distance(user_vector).label('distance')

query = (
    select(Article, ArticleMetadata, similarity)
    .join(ArticleMetadata, Article.id == ArticleMetadata.article_id)
    .order_by(similarity)
    .limit(10)
)
```

---

## 4. API Endpoint Construction (`GET /api/articles/feed`)

### API Specification:
- **Route**: `GET /api/articles/feed`
- **Protection**: Requires valid JWT (User must be authenticated).
- **Query Params**: `limit` (default 10), `days_back` (default 2).

### 4.1 Request Flow:
1. Validate JWT and extract `user_id`.
2. Query `user_profiles` to get the `interest_embedding`. If it is NULL, return a 400 error asking the user to complete onboarding (Phase 2).
3. Execute the vector similarity search query.
4. Transform the `distance` score into a friendly `match_percentage` (e.g., `(1 - distance) * 100`).

### 4.2 Response Formatting:
The frontend expects a clean, flattened JSON array.
```json
{
  "feed": [
    {
      "article_id": "uuid-1234",
      "title": "New Tech Breakthrough",
      "source": "TechCrunch",
      "published_date": "2026-08-01T12:00:00Z",
      "match_percentage": 92.5,
      "bias": "Center",
      "bias_score": -0.1,
      "credibility": 0.9,
      "reasoning": "Matches your interest in Technology"
    }
  ]
}
```
*Note*: The `bias` string ("Left", "Center", "Right") should be calculated on the fly by the backend based on the float `bias_score`. (e.g., `< -0.3` is Left, `> 0.3` is Right).

---

## 5. Validation & Verification Steps
Before considering Phase 5 complete, the executing agent MUST verify the following:
1. **Speed Test**: The `/feed` endpoint must return results in under 500ms. If it is performing a sequential scan instead of using the HNSW index, check the SQLAlchemy query output via `EXPLAIN`.
2. **Relevance Test**: Create a dummy user profile with an `interest_embedding` heavily skewed toward "Sports". Call the `/feed` endpoint. Ensure the top returned articles are sports-related and have a high `match_percentage`.
3. **Empty State Handling**: Ensure the endpoint gracefully handles the scenario where no articles exist in the database for the last 48 hours (it should return an empty array, not a 500 server error).

---

## 6. Architectural Constraints to Remember
- **Do not fetch the `content` payload**: To keep the feed API blazing fast, do not `SELECT a.content`. The frontend only needs the `title`, `source`, and metadata for the feed view. Create a separate endpoint (e.g., `GET /api/articles/{id}`) to fetch the heavy full text when the user actually clicks an article.
- **Index Usage**: CockroachDB will only use the HNSW index for `ORDER BY` operations combined with `LIMIT`. Do not add complex `WHERE` clauses on the `articles` table that might prevent the index from being utilized efficiently.

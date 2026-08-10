# Phase 8: Echo Chamber Detection & Contrarian Search

## 1. Phase Overview and Objectives
Phase 8 implements the "Show me the other side" feature. This is the core hackathon differentiator. When a user feels an article is too one-sided, or if the agent proactively wants to challenge them, the system must perform a highly specific vector search to find an article on the *exact same topic*, but from an *opposing viewpoint*.

**Objectives for the AI Agent executing this phase:**
- [ ] Build the `POST /api/agent/opposing-view` endpoint.
- [ ] Implement the complex CockroachDB query to find semantically similar but ideologically opposed articles.
- [ ] Integrate the frontend button to trigger this endpoint and display the result.

---

## 2. Prerequisites & Environment Setup
Requires Phase 1 (Schema), Phase 4 (Embeddings and Bias Scores), and Phase 5 (Vector Search).

No new packages are required.

---

## 3. The Contrarian Vector Search Logic

Finding an opposing view is a delicate balance. If we just reverse the user's vector, we might give them an article about "Sports" when they were reading about "Politics". We must anchor the search to the *current article's topic*, but flip the *bias*.

### 3.1 The Query Strategy
1. **Anchor**: Take the `article_embedding` of the source article.
2. **Semantic Similarity**: Find articles in the database with a high cosine similarity to the anchor (e.g., > 0.85). This ensures they are talking about the exact same specific news event.
3. **Bias Delta**: Filter those results to only include articles where the `bias_score` is on the opposite side of the spectrum.
   - If Source Bias is `-0.6` (Left), target articles with Bias `> 0.2` (Center-Right to Right).
   - If Source Bias is `0.5` (Right), target articles with Bias `< -0.1` (Center-Left to Left).

### 3.2 SQL Equivalent
```sql
SELECT a.id, a.title, m.bias_score,
       1 - (a.article_embedding <=> '<source_article_vector>') AS similarity
FROM articles a
JOIN article_metadata m ON a.id = m.article_id
WHERE a.id != '<source_article_id>'
  AND (1 - (a.article_embedding <=> '<source_article_vector>')) > 0.85
  AND m.bias_score > 0.2 -- Assuming source was Left-leaning
ORDER BY similarity DESC, m.source_credibility DESC
LIMIT 1;
```

### 3.3 Implementation Requirement (FastAPI)
The agent must implement this dynamically using SQLAlchemy. The query must automatically determine the target bias range based on the source article's metadata.

---

## 4. API Endpoint (`POST /api/agent/opposing-view`)

### API Specification:
- **Route**: `POST /api/agent/opposing-view`
- **Protection**: Requires JWT.

**Request Payload:**
```json
{
  "article_id": "uuid"
}
```

**Response Payload:**
Returns a single article object (the best opposing match) or a 404 if no opposing view on that specific topic exists in the Tier 1 cache.
```json
{
  "article_id": "uuid-9999",
  "title": "A Different Take on the Climate Bill",
  "bias": "Right",
  "bias_score": 0.6,
  "credibility": 0.88,
  "similarity": 0.91
}
```

---

## 5. Frontend Integration
The React app must wire up the "🔄 Show me the other side" button in the Article Reading View.

### 5.1 UI Flow:
1. User clicks the button.
2. Button shows a loading spinner.
3. Call `apiClient.post('/api/agent/opposing-view', { article_id })`.
4. If a match is found, render a new "Perspective Challenge" card below the current article, displaying the opposing article's title, source, and bias.
5. If a 404 is returned, show a gentle toast message: *"No opposing viewpoints found for this specific story yet."*

---

## 6. Validation & Verification Steps
Before considering Phase 8 complete, the executing agent MUST verify the following:
1. **Database Seeding**: You MUST have at least two articles in CockroachDB about the exact same topic (e.g., "Tax Cuts") but with different bias scores (e.g., one -0.7, one 0.8). Ensure their vectors are semantically similar.
2. **API Test**: Call the endpoint passing the ID of the Left-leaning article. Verify that it returns the Right-leaning article.
3. **Similarity Threshold Test**: Attempt the call on an article that has no semantic matches in the database. Ensure it returns a 404 instead of randomly returning an unrelated article just because the bias is opposite.
4. **Frontend Check**: Click the button in the UI and ensure the transition to showing the opposing article is smooth and handles errors gracefully.

---

## 7. Architectural Constraints to Remember
- **Vector Index Limits**: Because we are combining a strict vector similarity threshold (`> 0.85`) with a scalar `WHERE` filter (`bias_score > X`), CockroachDB may struggle to use the HNSW index effectively if the dataset is small. For the hackathon scale, this is fine, but in production, filtering *after* a KNN search is standard practice.
- Do not let the similarity threshold drop too low (e.g., below 0.7), or the "opposing view" will be a completely unrelated news story, ruining the user experience.

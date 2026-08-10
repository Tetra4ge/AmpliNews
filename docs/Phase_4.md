# Phase 4: AI Processing & Lazy Embeddings (Groq)

## 1. Phase Overview and Objectives
Phase 4 introduces the intelligence layer to our raw news cache. Generating 1536-dimensional vectors for every single article on the internet is prohibitively expensive. Therefore, we use **Lazy Embedding Generation**.

In this phase, the agent will build a service that scans the CockroachDB `articles` table for records that lack an `article_embedding` or `article_metadata`. It will then use the **Groq API** (running a fast model like Llama 3) to analyze the text for bias and sentiment, and an embedding model (via HuggingFace or OpenAI/Groq) to generate the vector.

**Objectives for the AI Agent executing this phase:**
- [ ] Integrate the Groq API client into the FastAPI backend.
- [ ] Write the system prompts to classify an article's `bias_score` (-1.0 to 1.0) and `sentiment`.
- [ ] Integrate an embedding provider to generate the `VECTOR(1536)`.
- [ ] Create the `metadata_enrichment` service to process pending articles.
- [ ] Store the generated vectors and metadata back into CockroachDB.

---

## 2. Prerequisites & Environment Setup
Ensure the LLM API keys are configured.

**Required Environment Variables:**
```env
GROQ_API_KEY="<your-groq-api-key>"
# If using a separate embedding provider (e.g., OpenAI or Cohere)
EMBEDDING_API_KEY="<your-embedding-key>" 
```

**Required Python Packages (`backend/requirements.txt`):**
```text
groq==0.4.2
langchain-groq==0.0.1
# If using local embeddings to save money:
sentence-transformers==2.5.1 
```

---

## 3. Bias & Sentiment Analysis via Groq
The agent must create a dedicated LLM service (`backend/app/services/llm_analysis.py`). Because we need structured output (a float for bias, a string for sentiment), the agent should use Groq's JSON mode or LangChain's structured output parsers.

### 3.1 The System Prompt
The prompt must be highly deterministic. 
- **Bias Score**: Must be a float between -1.0 (Extreme Left/Liberal bias) and +1.0 (Extreme Right/Conservative bias). 0.0 is perfectly neutral.
- **Sentiment**: Must be an enum or string (e.g., "Positive", "Negative", "Neutral", "Alarmist").
- **Source Credibility**: Estimate a float between 0.0 and 1.0 based on the source name and journalistic standards.

**Implementation Requirement (Schema):**
```python
from pydantic import BaseModel, Field

class ArticleAnalysis(BaseModel):
    bias_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment: str = Field(...)
    source_credibility: float = Field(..., ge=0.0, le=1.0)
    topic: str = Field(...)
```

### 3.2 Executing the Groq Call
Pass the article's `title` and `content` to Groq (`llama3-8b-8192` or `mixtral-8x7b-32768` for speed) and parse the JSON response into the `ArticleAnalysis` schema.

---

## 4. Lazy Embedding Generation
After Groq analyzes the article, we must generate its vector representation so it can be searched via `pgvector`.

### 4.1 Embedding Strategy
- If using `sentence-transformers` locally, ensure the model outputs 1536 dimensions (or update the CockroachDB schema if using a 384-dimensional model like `all-MiniLM-L6-v2`).
- *Note for Agent*: If you change the dimension size in this phase, YOU MUST go back and update the SQLAlchemy models in Phase 1 to match the new dimension size, and drop/recreate the tables in CockroachDB.

### 4.2 The Enrichment Service
Create a background task or a script (`backend/app/services/enrichment.py`) that performs the following:
1. Query CockroachDB: `SELECT * FROM articles WHERE article_embedding IS NULL LIMIT 50;`
2. For each article, call the Groq analysis service.
3. Call the Embedding service on the text: `f"{title}. {content}"`
4. Update the `articles` table with the new `article_embedding`.
5. Insert a new row into the `article_metadata` table with the Groq results.
6. Commit the SQLAlchemy session.

---

## 5. API Trigger Endpoint
Create an endpoint to manually trigger the enrichment process.

### API Specification:
- **Route**: `POST /api/admin/enrich`
- **Protection**: Requires admin JWT.
- **Action**: Processes up to 50 pending articles.
- **Returns**: 
```json
{
  "status": "success",
  "articles_processed": 50,
  "remaining_pending": 120
}
```

---

## 6. Validation & Verification Steps
Before considering Phase 4 complete, the executing agent MUST verify the following:
1. **Groq Parsing**: Send a known heavily biased article text to the Groq service. Assert that the returned `bias_score` is correctly skewed (e.g., > 0.5 or < -0.5).
2. **Embedding Size**: Assert that the generated `len(vector)` matches the exact dimension size defined in the CockroachDB schema.
3. **End-to-End Test**: Hit the `/api/admin/enrich` endpoint. Check CockroachDB to ensure the `article_embedding` column is no longer NULL for those rows, and that the `article_metadata` table contains the matching rows.
4. **Performance Check**: The enrichment of 10 articles should take less than 15 seconds. If it takes longer, consider utilizing asynchronous `asyncio.gather` calls for the Groq API.

---

## 7. Architectural Constraints to Remember
- **Rate Limits**: Groq has strict rate limits for free tiers. The agent MUST implement a `try/except` block with exponential backoff (`tenacity` library recommended) to handle HTTP 429 Too Many Requests errors gracefully during batch enrichment.
- **Separation of Concerns**: Do not combine the Tier 1 ingestion script (Phase 3) with this enrichment script (Phase 4). They must remain decoupled so they can scale independently in AWS Lambda later.

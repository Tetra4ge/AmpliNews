# Technical Requirements Document (TRD)
**Project Name**: AmpliNews: Personalized News Digest Agent with Bias Detection
**Version**: 1.0.0

---

## 1. Introduction & Scope
This Technical Requirements Document outlines the architecture, data structures, API endpoints, agent state machines, and deployment strategies for **AmpliNews**. The system relies on a React frontend, a FastAPI backend, Groq for LLM inference, LangGraph for agent orchestration, and CockroachDB as the persistent memory and vector datastore.

## 2. System Architecture Overview
The system is divided into four main logical blocks:
1. **Client Application (Frontend)**: A React SPA that securely communicates with the backend via REST and manages user state through Supabase.
2. **Backend Gateway (FastAPI)**: Routes requests, manages synchronous interactions, and kicks off asynchronous agent tasks.
3. **Agent Orchestration (LangGraph + Groq)**: A stateful, multi-node graph that performs complex workflows (e.g., Echo Chamber detection, vector search, digest synthesis) using CockroachDB Agent Skills.
4. **Data & Storage Layer (CockroachDB & AWS)**: CockroachDB Serverless handles relational data and distributed vector embeddings. AWS provides blob storage (S3), compute triggers (EventBridge/Lambda), and email dispatch (SES).

---

## 3. Database Schema & Agentic Memory (CockroachDB)

The database utilizes the `pgvector` extension to allow the agent to perform semantic similarity searches natively. 

### 3.1 `articles`
- `id` (UUID, Primary Key)
- `title` (TEXT)
- `content` (TEXT)
- `source` (TEXT)
- `published_date` (TIMESTAMPTZ)
- `article_embedding` (VECTOR(1536))
- *Index*: HNSW index on `article_embedding` for `vector_cosine_ops`.

### 3.2 `article_metadata`
- `article_id` (UUID, Foreign Key)
- `bias_score` (FLOAT, Range -1.0 to 1.0)
- `sentiment` (VARCHAR)
- `source_credibility` (FLOAT, Range 0.0 to 1.0)
- `topic` (VARCHAR)

### 3.3 `user_profiles` (The Core "Memory")
- `user_id` (UUID, Foreign Key to Supabase Auth)
- `interest_embedding` (VECTOR(1536)) - Continuously updated via vector addition based on reading history.
- `political_leaning` (FLOAT, Range -1.0 to 1.0)
- `created_at` (TIMESTAMPTZ)

### 3.4 `reading_history`
- `id` (UUID, Primary Key)
- `user_id` (UUID)
- `article_id` (UUID)
- `read_duration_seconds` (INT)
- `liked` (BOOLEAN)
- `timestamp` (TIMESTAMPTZ)

### 3.5 `agent_memory`
- `id` (UUID, Primary Key)
- `user_id` (UUID)
- `memory_key` (VARCHAR)
- `memory_value` (TEXT) - e.g., "User rejected center-left tech article on 2026-08-01".

---

## 4. API Specifications (FastAPI)

### 4.1 Authentication & User Management
- `POST /api/auth/sync`: Syncs the Supabase user creation with the CockroachDB `user_profiles` table and initializes a generic `interest_embedding`.
- `GET /api/user/{user_id}/insights`: Returns the user's current diversity score and political leaning based on their reading history.

### 4.2 News Feed
- `GET /api/articles/feed`
  - **Auth**: Requires JWT.
  - **Action**: Performs a vector search against CockroachDB `articles` using the user's `interest_embedding`.
  - **Returns**: Array of localized article objects with metadata.
- `POST /api/articles/read`
  - **Payload**: `{ "article_id": "uuid", "duration": 120, "liked": true }`
  - **Action**: Logs to `reading_history` and triggers an async background task to recalculate the user's `interest_embedding`.

### 4.3 Agent Interactions
- `POST /api/agent/opposing-view`
  - **Payload**: `{ "article_id": "uuid" }`
  - **Action**: Queries CockroachDB for articles with a cosine similarity > 0.85 to the original article, but with a `bias_score` delta of at least 0.5.

---

## 5. Agentic Orchestration (LangGraph)

The core brain of AmpliNews is defined by a state graph that handles the daily digest generation and echo chamber interventions.

### 5.1 Graph State Definition
```python
class AgentState(TypedDict):
    user_id: str
    user_profile: dict
    reading_history: list
    echo_chamber_detected: bool
    recommended_articles: list
    contrarian_articles: list
    final_digest: str
```

### 5.2 Nodes
1. **RetrieveContextNode**: Executes CockroachDB Agent Skills to fetch `user_profiles` and the last 7 days of `reading_history`.
2. **BiasAnalysisNode**: Calculates the average bias of read articles. If the standard deviation is extremely low, `echo_chamber_detected = True`.
3. **StandardRetrievalNode**: Uses pgvector to find the top 5 relevant articles based on `interest_embedding`.
4. **ContrarianRetrievalNode**: Conditional node. If `echo_chamber_detected` is true, performs a vector search for articles mapped to the user's favorite topics but originating from opposing sources.
5. **SynthesisNode**: Uses Groq (Llama-3/Mixtral) to write the final HTML/Markdown digest, explaining *why* the contrarian view was included.

---

## 6. Data Pipeline (Ingestion)

1. **Trigger**: AWS EventBridge triggers an ingestion script hourly.
2. **Fetch**: Pulls data from NewsAPI and curated RSS feeds.
3. **Process (Groq)**: 
   - Classifies topic.
   - Determines sentiment and bias score (-1.0 to 1.0).
4. **Embed (HuggingFace / Groq API)**: Generates a 1536-dimensional vector for the article text.
5. **Store**: Persists the raw text to AWS S3 (for backup) and inserts the vector + metadata into CockroachDB.

---

## 7. Infrastructure & Deployment

### 7.1 AWS Integration
- **Lambda**: Hosts the cron-triggered ingestion and digest generation scripts.
- **EventBridge**: Cron schedules (`cron(0 * * * ? *)` for ingestion, `cron(0 8 * * ? *)` for digests).
- **S3**: `s3://amplinews-archive-store` configured with lifecycle policies to move raw text to Glacier after 30 days.
- **SES**: Domain verified. Invoked by the SynthesisNode to email users.

### 7.2 Core Services
- **Database**: CockroachDB Serverless deployed in the matching AWS Region to minimize latency.
- **Backend API**: Containerized via Docker, deployed to Render or AWS ECS.
- **Frontend App**: Vercel or AWS Amplify.

---

## 8. Security & Environment Variables

- **JWT Validation**: All FastAPI endpoints (except webhooks) require a valid Supabase JWT Bearer token.
- **CockroachDB SSL**: Must use `sslmode=verify-full` with the downloaded CA certificate for the Serverless cluster.
- **Required Env Variables**:
  - `DATABASE_URL`
  - `GROQ_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_JWT_SECRET`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`

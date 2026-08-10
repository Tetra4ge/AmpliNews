# Phase 1: Database & Memory Layer Setup (CockroachDB & pgvector)

## 1. Phase Overview and Objectives
Phase 1 focuses on establishing the core "brain" of the AmpliNews application. We will configure a **CockroachDB Serverless** cluster, enable the `pgvector` extension for distributed vector search, and define the complete relational and vector database schema. 

This phase is critical because all agent reasoning, echo chamber detection, and semantic search relies entirely on the structure and performance of this database layer. 

**Objectives for the AI Agent executing this phase:**
- [ ] Connect the backend (Python/SQLAlchemy) securely to CockroachDB.
- [ ] Enable `pgvector` on the default database.
- [ ] Create the declarative SQLAlchemy models for all six core tables.
- [ ] Configure HNSW (Hierarchical Navigable Small World) indexes on vector columns to ensure sub-2-second retrieval.
- [ ] Set up Alembic for database migrations.

---

## 2. Prerequisites & Environment Setup
Before writing the database models, ensure the environment is correctly configured.

**Required Environment Variables (in `backend/.env`):**
```env
# Must use sslmode=verify-full for CockroachDB Serverless
DATABASE_URL="postgresql://<user>:<password>@<host>:26257/defaultdb?sslmode=verify-full"
```

**Required Python Packages (`backend/requirements.txt`):**
```text
fastapi==0.109.2
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pgvector==0.2.5
alembic==1.13.1
cockroachdb==0.3.3
```

---

## 3. Database Connection & Base Setup
The agent should create a `backend/app/db/session.py` file to manage the SQLAlchemy engine and sessions. 

### Critical Connection Rules for CockroachDB:
1.  **Driver**: Use `postgresql+psycopg2://` in the engine URL.
2.  **Pool Pre-ping**: Set `pool_pre_ping=True` to handle serverless connection drops gracefully.
3.  **Vector Extension**: The agent MUST run the raw SQL command `CREATE EXTENSION IF NOT EXISTS vector;` before creating the tables.

---

## 4. Detailed Schema Definitions (SQLAlchemy Models)
The agent must create these models in `backend/app/models/`.

### 4.1 The `Article` Model (`models/article.py`)
This represents the Tier 1 Hot Cache.
- `id`: `UUID(as_uuid=True)`, primary key, default `uuid.uuid4`.
- `title`: `String(255)`, nullable=False.
- `content`: `Text`, nullable=False.
- `source`: `String(100)`, nullable=False.
- `published_date`: `DateTime(timezone=True)`.
- `article_embedding`: `Vector(1536)`. This must use the `Vector` type from the `pgvector.sqlalchemy` package.
- **Index**: Create an HNSW index on `article_embedding`.

### 4.2 The `ArticleMetadata` Model (`models/article_metadata.py`)
- `id`: `UUID`, primary key.
- `article_id`: `UUID`, Foreign Key to `articles.id`.
- `bias_score`: `Float`. Range is -1.0 (Extreme Left) to +1.0 (Extreme Right).
- `sentiment`: `String(50)`.
- `source_credibility`: `Float`. Range 0.0 to 1.0.
- `topic`: `String(100)`.

### 4.3 The `UserProfile` Model (`models/user_profile.py`)
This is the core of the Agent's memory regarding the user.
- `user_id`: `UUID`, primary key (maps to Supabase Auth ID).
- `interest_embedding`: `Vector(1536)`. Used to find relevant articles. 
- `baseline_political_leaning`: `Float` (-1.0 to 1.0).
- `created_at`: `DateTime(timezone=True)`.

### 4.4 The `ReadingHistory` Model (`models/reading_history.py`)
Logs every interaction to calculate echo chambers later.
- `id`: `UUID`, primary key.
- `user_id`: `UUID`, Foreign Key to `user_profiles.user_id`.
- `article_id`: `UUID`, Foreign Key to `articles.id`.
- `read_duration_seconds`: `Integer`.
- `liked`: `Boolean`.
- `timestamp`: `DateTime(timezone=True)`.

### 4.5 The `PerspectivePair` Model (`models/perspective_pair.py`)
Used to quickly link two opposing articles.
- `id`: `UUID`, primary key.
- `article_id_a`: `UUID`.
- `article_id_b`: `UUID`.
- `topic`: `String(100)`.
- `similarity_score`: `Float`.

### 4.6 The `AgentMemory` Model (`models/agent_memory.py`)
Stores discrete textual observations made by the LangGraph agent.
- `id`: `UUID`, primary key.
- `user_id`: `UUID`, Foreign Key to `user_profiles.user_id`.
- `memory_key`: `String(100)`. (e.g., "rejected_bias_threshold")
- `memory_value`: `Text`. (e.g., "User consistently swipes away articles with a bias > 0.8")

---

## 5. HNSW Vector Indexing Implementation
When defining the `Article` model, the AI agent MUST include the HNSW index declaration to ensure fast nearest-neighbor search.

**Example Implementation Requirement:**
```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Index

class Article(Base):
    __tablename__ = 'articles'
    # ... other columns ...
    article_embedding = Column(Vector(1536))
    
    __table_args__ = (
        Index(
            'ix_articles_embedding_hnsw',
            'article_embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'article_embedding': 'vector_cosine_ops'}
        ),
    )
```

---

## 6. Alembic Migrations
The agent must initialize Alembic (`alembic init alembic`) and configure `alembic/env.py` to:
1. Load the `DATABASE_URL` from the `.env` file.
2. Import all SQLAlchemy models.
3. Automatically generate the initial migration script (`alembic revision --autogenerate -m "Initial schema"`).

---

## 7. Validation & Verification Steps
Before considering Phase 1 complete, the executing agent MUST verify the following:
1. Can the backend successfully connect to CockroachDB without SSL errors?
2. Does the `vector` extension exist in the database?
3. Were all tables successfully created via Alembic?
4. **Crucial Test**: The agent must write a quick Python script to insert a dummy article with a 1536-dimensional array of zeros, and query it back using a cosine similarity `L2_distance` check to prove `pgvector` is functioning correctly.

---

## 8. Architectural Constraints to Remember
*Reference `docs/Cockroach DB Limitations.pdf`*
- Do **not** plan to store raw text in CockroachDB indefinitely. The `Article` table is our "Tier 1 Hot Cache". 
- Future phases (Phase 10) will implement lifecycle policies to strip the `article_embedding` and move the `content` to S3 after 30 days. For Phase 1, just focus on building the hot cache schemas.

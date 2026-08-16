<h1 align="center">AmpliNews: Personalized News Digest Agent with Bias Detection</h1>

An intelligent, agentic news curator designed to combat political polarization and algorithmic echo chambers. Built for the **CockroachDB × AWS Hackathon**.

## The Problem
Social media algorithms optimize for engagement by feeding users content that aligns with their pre-existing beliefs, creating dangerous "echo chambers". Over time, this leads to polarization and a lack of exposure to diverse perspectives.

<div align="center">
  <img src="https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB" alt="React" />
  <img src="https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/CockroachDB-6933FF?style=for-the-badge&logo=cockroachlabs&logoColor=white" alt="CockroachDB" />
  <img src="https://img.shields.io/badge/pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="pgvector" />
  <img src="https://img.shields.io/badge/bge--small--en--v1.5-F9AB00?style=for-the-badge&logo=huggingface&logoColor=white" alt="bge-small-en-v1.5" />
  <img src="https://img.shields.io/badge/llama--3.1--8b--instant-0466C8?style=for-the-badge&logo=meta&logoColor=white" alt="Llama 3.1 8b" />
  <img src="https://img.shields.io/badge/AWS_Lambda-%23FF9900.svg?style=for-the-badge&logo=awslambda&logoColor=white" alt="AWS Lambda" />
  <img src="https://img.shields.io/badge/AWS_EventBridge-%238C4FFF.svg?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS EventBridge" />
  <img src="https://img.shields.io/badge/AWS_S3-%23569A31.svg?style=for-the-badge&logo=amazons3&logoColor=white" alt="AWS S3" />
  <img src="https://img.shields.io/badge/AWS_SES-%230073BB.svg?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS SES" />
</div>

## Our Solution
The **AmpliNews** agent learns your reading habits and interests to deliver relevant news—but actively monitors for bias. If it detects that you are falling into a filter bubble (e.g., only reading left-leaning or right-leaning articles), it deliberately retrieves and suggests high-quality, contrarian articles on the same topics to challenge your perspective.

## Architecture & Tech Stack

This project leverages a modern, serverless agentic stack:

```mermaid
graph TD
    User([User]) --> UI[React + Vite UI]
    UI <--> |Auth| Supa[(Supabase Auth)]
    UI --> |REST API| API[FastAPI Backend]
    
    subgraph Agent Loop [LangGraph + Groq Agent]
        direction TB
        API --> Context[Retrieve Context]
        Context --> Search[Vector Search]
        Search --> Detect{Echo Chamber?}
        Detect -- Yes --> Contrarian[Fetch Contrarian Views]
        Detect -- No --> Synth[Synthesize Digest]
        Contrarian --> Synth
    end
    
    Synth <--> |Agent Skills| DB[(CockroachDB: pgvector)]
    Context <--> |SQL| DB
    Search <--> |Similarity Match| DB
    
    Synth --> S3[(AWS S3: Backups)]
    
    Cron[AWS EventBridge] --> Lambda[AWS Lambda]
    Lambda --> API
    Lambda --> SES[AWS SES: Email Digest]
```

## Backend Data Flow

```mermaid
graph TD
    classDef ingest fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff;
    classDef agent fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff;
    classDef db fill:#FF9800,stroke:#EF6C00,stroke-width:2px,color:#fff;
    classDef output fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px,color:#fff;

    Start((News Ingestion)):::ingest --> Fetch[Fetch RSS Feeds]:::ingest
    Fetch --> Embed[Generate Embeddings]:::ingest
    Embed --> StoreDB[(Save to CockroachDB)]:::db

    Trigger((User Requests Feed)):::agent --> Auth[Validate User]:::agent
    Auth --> Profile[Retrieve Profile Vector]:::db
    Profile --> SimSearch[Vector Similarity Search]:::db
    
    SimSearch --> EchoCheck{Is User in an Echo Chamber?}:::agent
    
    EchoCheck -- "Yes (Bias Detected)" --> FetchOp[Fetch Contrarian Viewpoints]:::agent
    EchoCheck -- "No (Balanced)" --> Synthesize[Synthesize Regular Digest]:::agent
    
    FetchOp --> Blend[Blend Contrarian & Personalized Articles]:::agent
    Blend --> Synthesize
    
    Synthesize --> Return((Return News Feed)):::output
    Synthesize --> Memory[(Update Agent Memory)]:::db
```

### Agent & AI Layer
*   **Groq**: Lightning-fast LLM inference using **`llama-3.1-8b-instant`** for agent reasoning, topic classification, and sentiment/bias analysis.
*   **LangGraph**: Orchestrates the multi-agent workflow (Context Retrieval ➔ Similarity Search ➔ Bubble Detection ➔ Contrarian Search ➔ Digest Synthesis).

### Data & Memory Layer (CockroachDB)
*   **CockroachDB Cloud Serverless**: Acts as the central, persistent memory layer for the entire application.
*   **Distributed Vector Indexing**: We store both article embeddings and user interest vectors in CockroachDB using `pgvector`. This allows lightning-fast semantic search to match users with relevant news.
*   **Agent Skills Repo**: The Groq agent utilizes pre-built CockroachDB Agent Skills to dynamically query user profiles, read reading history, and perform vector similarity searches safely.

### AWS Infrastructure
*   **Amazon S3**: Used as our scalable file storage and data lake to back up raw ingested articles and archive generated daily digest snapshots.

### Web Stack
*   **Backend**: FastAPI (Python 3.11+) handles API orchestration and agent invocation.
*   **Frontend**: React 19 + Vite + Tailwind CSS provides a premium, interactive user dashboard displaying bias metrics and the curated news feed.
*   **Auth**: Supabase handles secure user authentication and session management.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- CockroachDB Cloud Account (Serverless)
- AWS Account (S3)
- Groq API Key
- Supabase Account

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set up your `.env` file in the `backend/` directory:
   ```env
   # Server Configuration
   PORT=8000
   HOST=0.0.0.0
   FRONTEND_URL=http://localhost:5173

   # CockroachDB Serverless (pgvector enabled)
   DATABASE_URL="postgresql://user:password@host:26257/defaultdb?sslmode=verify-full"

   # Supabase (Authentication & JWT Validation)
   SUPABASE_URL="https://your-project-id.supabase.co"
   SUPABASE_JWT_SECRET="your-jwt-secret"
   SUPABASE_JWT_AUDIENCE="authenticated"

   # LLM & Agent Orchestration (Groq)
   GROQ_API_KEY="gsk_your_groq_api_key_here"

   # AWS Infrastructure (S3, Lambda, EventBridge, SES)
   AWS_ACCESS_KEY_ID="your_aws_access_key"
   AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
   AWS_REGION="us-east-1"
   AWS_S3_BUCKET_NAME="amplinews-archive-store"
   AWS_SES_SENDER_EMAIL="digest@yourdomain.com"

   # Embedding Model (HuggingFace)
   HF_API_KEY="your_hf_api_key_here"

   # News Ingestion
   NEWS_API_KEY="your_news_api_key_here"

   # Manual admin trigger for the ingestion pipeline
   ADMIN_SECRET_KEY="change_me_to_a_random_secret"
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up your `.env` file in the `frontend/` directory:
   ```env
   VITE_API_DEV_URL=http://127.0.0.1:8000
   VITE_API_PRO_URL=https://your-production-backend.com

   VITE_MODE=development

   VITE_SUPABASE_URL=https://your-project-id.supabase.co
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```

## Hackathon Compliance
*   **Agentic App**: Fully autonomous LangGraph workflow (`backend/agent/graph.py`) that dynamically retrieves reading history, calculates echo chamber risk, curates personalized & contrarian perspectives, and synthesizes daily HTML digests using Groq.
*   **Serverless AWS Lambda**: Includes an AWS Lambda handler entrypoint (`backend/lambda_handler.py`) and AWS SES integration (`backend/services/email.py`).
*   **CockroachDB Tools**: Uses **Distributed Vector Indexing** (HNSW pgvector) for semantic search and CockroachDB tables for stateful agentic memory.
*   **AWS Services**: Uses **Amazon S3** (`amplinews-archive-store`) for cold storage article archival, **AWS Lambda** for serverless graph orchestration, and **AWS SES** for automated daily digest delivery.
*   **Tiered Storage & Offloading**: Implements automated database offloading (`backend/services/archival.py`). Articles older than 30 days are archived to AWS S3 as compressed JSON payloads, nullifying heavy 384d vector embeddings in CockroachDB to preserve HNSW index performance while allowing seamless transparent retrieval upon user request.
*   **Persistent Memory**: CockroachDB fundamentally powers the agent's ability to track user reading patterns and update `interest_embedding` vectors over time.

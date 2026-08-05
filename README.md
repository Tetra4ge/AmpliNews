<h1 align="center">Personalized News Digest Agent with Bias Detection</h1>

An intelligent, agentic news curator designed to combat political polarization and algorithmic echo chambers. Built for the **CockroachDB × AWS Hackathon**.

## The Problem
Social media algorithms optimize for engagement by feeding users content that aligns with their pre-existing beliefs, creating dangerous "echo chambers". Over time, this leads to polarization and a lack of exposure to diverse perspectives.

## Our Solution
The **Personalized News Digest Agent** learns your reading habits and interests to deliver relevant news—but actively monitors for bias. If it detects that you are falling into a filter bubble (e.g., only reading left-leaning or right-leaning articles), it deliberately retrieves and suggests high-quality, contrarian articles on the same topics to challenge your perspective.

## Architecture & Tech Stack

This project leverages a modern, serverless agentic stack:

### Agent & AI Layer
*   **Groq**: Lightning-fast LLM inference (Llama/Mixtral) used for agent reasoning, topic classification, and sentiment/bias analysis.
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
3. Set up your `.env` file based on `.env.example`.
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
3. Set up your `.env` file with your API URL and Supabase credentials.
4. Start the Vite development server:
   ```bash
   npm run dev
   ```

## Hackathon Compliance
*   **Agentic App**: Fully autonomous LangGraph workflow that dynamically retrieves data and reasons about user bias.
*   **CockroachDB Tools**: Uses **Distributed Vector Indexing** for semantic search and the **CockroachDB Agent Skills Repo** for memory access.
*   **AWS Services**: Uses **Amazon S3** for artifact and document storage.
*   **Persistent Memory**: CockroachDB is not just an afterthought; it fundamentally powers the agent's ability to remember what users read and track their shifting political leanings over time.
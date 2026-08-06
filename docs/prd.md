# Product Requirements Document (PRD)
**Project Name**: AmpliNews: Personalized News Digest Agent with Bias Detection
**Event**: CockroachDB × AWS Hackathon
**Version**: 1.0.0

---

## 1. Executive Summary
AmpliNews is an intelligent, agent-driven news curator designed to combat the rising tide of political polarization and algorithmic echo chambers. Traditional social media platforms optimize for engagement by feeding users content that strictly aligns with their pre-existing beliefs. Over time, this leads to significant polarization. 

AmpliNews solves this by tracking a user's reading habits and understanding their interests, delivering highly relevant news while *actively* monitoring for ideological bias. When the agent detects that a user is falling into a filter bubble, it deliberately retrieves and suggests high-quality, contrarian articles on identical topics to challenge the user's perspective, thus fostering a healthier media diet.

## 2. Target Audience
- **News Enthusiasts**: People who read news daily but are frustrated by the inherent bias of single sources.
- **Politically Minded Individuals**: Users who want to understand multiple sides of a political or social issue without hunting down opposing articles manually.
- **Researchers & Academics**: Professionals who need a holistic view of current events across the entire political spectrum.

---

## 3. Core Features & Capabilities

### 3.1 Personalized News Feed
- **Interest Selection**: Users select their interests (e.g., Politics, Tech, Health, Business) and baseline political leaning during onboarding.
- **Semantic Matching**: The agent utilizes vector search to find articles that match the user's explicit interests and implicit reading behaviors.
- **Dynamic Scoring**: Every article displayed includes a relevance match percentage (e.g., "95% match"), a bias indicator (Left, Center, Right), and a source credibility score.

### 3.2 Echo Chamber Detection (The Agentic Core)
- **Behavioral Tracking**: The system tracks which articles a user clicks, their scroll depth, and total reading time. 
- **Bias Analysis**: The LangGraph agent continuously calculates a rolling average of the user's consumed media bias. 
- **Bubble Alert**: If the user heavily skews toward a single perspective (e.g., 75% Right-leaning sources over a 7-day period), the agent tags the user profile as being in an "Echo Chamber".

### 3.3 Contrarian Viewpoint Injection ("Show Me The Other Side")
- **In-App Toggle**: While reading an article, a user can click "Show me the other side". The agent instantly performs a similarity vector search to find an article covering the exact same topic from a different political lens.
- **Digest Intervention**: In the daily digest, if an echo chamber is detected, 30% of the curated articles are specifically chosen to present an opposing, highly credible viewpoint.

### 3.4 Daily AI-Generated Digest
- **Automated Delivery**: Triggered by AWS EventBridge and AWS Lambda every morning at 8:00 AM (user timezone).
- **Format**: A synthesized summary containing the top 5 personalized articles and 1-2 "Perspective Check" articles.
- **Distribution**: Sent directly to the user's email via AWS SES and available on the React dashboard.

### 3.5 Reading Analytics & Insights
- **User Dashboard**: A visual representation of the user's media diet, showing their "Bias Meter" (where they lean) and "Diversity Score" (how often they explore opposing views).
- **Feedback Loop**: Users can rate opposing views as "Helpful" or "Too biased". The agent incorporates this feedback to refine future recommendations.

---

## 4. Technical Architecture & Tech Stack

### 4.1 AI & Orchestration Layer
- **LLM Engine**: **Groq (Mixtral/Llama 3)** for ultra-fast, low-latency agent reasoning, sentiment analysis, and topic classification.
- **Agent Orchestrator**: **LangGraph** manages the stateful, multi-agent workflow consisting of Context Retrieval, Echo Chamber Detection, Vector Similarity Search, and Digest Synthesis.

### 4.2 Data & Persistent Memory Layer (CockroachDB)
CockroachDB acts as the persistent "brain" for the entire application. It is not just a datastore, but an active participant in agent reasoning.
- **Distributed Vector Indexing (`pgvector`)**: Stores dense vector embeddings for millions of news articles alongside dynamic user `interest_embedding` vectors.
- **Agent Skills Repo**: The Groq agent connects to CockroachDB using predefined Agent Skills (via MCP or direct tool calling) to safely retrieve context, execute complex vector queries, and update relational data.

### 4.3 AWS Infrastructure
- **Amazon S3**: Acts as the cold storage data lake, backing up raw ingested articles and archiving generated daily digests for historical reference.
- **AWS EventBridge**: A cron-based scheduler that triggers daily ingestion and digest generation routines.
- **AWS Lambda**: Executes serverless, stateless functions that kick off the LangGraph agent workflows.
- **AWS SES (Simple Email Service)**: Handles the reliable outbound delivery of personalized HTML news digests to users.

### 4.4 Web Stack
- **Backend API**: **FastAPI (Python 3.11+)** acts as the robust, asynchronous gateway connecting the frontend to the CockroachDB database and LangGraph agents.
- **Frontend App**: **React 19 + Vite + Tailwind CSS** delivers a premium, highly responsive user interface with animated bias meters and a clean reading experience.
- **Authentication**: **Supabase** handles secure JWT-based user authentication and basic session management.

---

## 5. High-Level Data Models

The system relies on six primary tables stored in CockroachDB:

1. `articles`: Stores the raw text, publication date, source, and an `article_embedding` (VECTOR).
2. `article_metadata`: Stores the calculated `bias_score` (Left/Center/Right scale), sentiment, and source credibility.
3. `user_profiles`: Stores the user's shifting `interest_embedding` (VECTOR) and baseline `political_leaning`.
4. `reading_history`: Logs every user interaction (article ID, read duration, scroll depth, like/dislike).
5. `perspective_pairs`: Maps opposing articles on identical topics for lightning-fast retrieval.
6. `agent_memory`: A dedicated table where the agent logs behavioral observations (e.g., "User rejected extreme-left article on climate change").

---

## 6. Success Metrics & Hackathon Goals
- **Performance**: Sub-2-second retrieval of contrarian articles using CockroachDB distributed vector indexing.
- **User Engagement**: Prove that the agent successfully updates the user's `interest_embedding` based on simulated reading history.
- **Hackathon Compliance**: 
  - [x] Uses CockroachDB for persistent memory.
  - [x] Utilizes CockroachDB Distributed Vectors.
  - [x] Utilizes CockroachDB Agent Skills Repo.
  - [x] Deployed/integrated with AWS services (S3, Lambda, EventBridge).

---

## 7. Future Roadmap (Post-Hackathon)
- **Live Agent Interactions**: Allow users to chat directly with the agent inside the app to debate topics.
- **Fact-Checking Module**: Integrate a secondary agent to cross-reference claims in highly biased articles against trusted knowledge bases.
- **Social Features**: Let users share their "Diversity Score" and media diet breakdown on social media to promote healthy news consumption.

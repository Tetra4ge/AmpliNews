# Project Guidelines: AmpliNews Agent End-to-End Flow

This workspace contains the **AmpliNews: Personalized News Digest Agent with Bias Detection** built for the CockroachDB × AWS Hackathon.
This document outlines the core agent logic and workflow that you must adhere to when generating backend logic, prompts, or frontend components.

## Core Reference
A detailed breakdown of the user experience and agent interactions is documented in **[docs/flow.md](file:///c:/HCK_THON/Cockroach_X_AWS/cockroach_X_aws/docs/flow.md)**. Always refer to this document to understand how the agent behaves in response to user actions.

## Key Agent Behaviors to Implement
1.  **Initial Profiling**: When users sign up, they select topics (Politics, Tech, etc.) and a political leaning (Left/Center/Right/Mixed). The agent must initialize a `user_profile` in CockroachDB with an initial `interest_embedding` vector.
2.  **Continuous Learning**: Every article read (duration, scroll depth, like/dislike) triggers an update to the user's `interest_embedding` in CockroachDB. This is the core of the "Agentic Memory".
3.  **Contrarian Views ("Show me the other side")**: If the user asks for the other side of a story, perform a vector search in CockroachDB for articles on the same topic but with an opposing bias score.
4.  **Daily Digest (Echo Chamber Detection)**: 
    *   The Lambda-triggered agent analyzes reading history (e.g., "User reads 70% Center sources").
    *   If a bubble is detected, the agent *must* allocate 30% of the digest to a "Perspective Check" (contrarian articles).
5.  **Weekly Insights**: The agent generates weekly progress reports showing how much the user's echo chamber has shrunk.

All logic revolves around saving state (vectors, bias scores, read history) in **CockroachDB**, querying it dynamically, and having the **LangGraph/Groq** agent act on that memory.

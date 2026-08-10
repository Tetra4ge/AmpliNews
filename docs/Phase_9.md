# Phase 9: LangGraph Agent & Daily Digest (AWS Lambda)

## 1. Phase Overview and Objectives
Phase 9 is the culmination of the AI logic. We will build a LangGraph state machine that executes daily for each user. It analyzes their reading history, detects if they are in an echo chamber, curates a personalized list of articles, injects contrarian viewpoints if necessary, and uses Groq to synthesize a friendly HTML email digest. 

**Objectives for the AI Agent executing this phase:**
- [ ] Define the LangGraph `StateGraph` and its nodes.
- [ ] Implement the `BiasAnalysisNode` to calculate the user's echo chamber risk.
- [ ] Implement the `SynthesisNode` using Groq to write the email copy.
- [ ] Create the AWS Lambda handler script to run the graph.
- [ ] Integrate AWS SES (Simple Email Service) to dispatch the email.

---

## 2. Prerequisites & Environment Setup
Requires all previous phases.

**Required Python Packages (`backend/requirements.txt`):**
```text
langgraph==0.0.26
langchain-core==0.1.23
boto3==1.34.40 # For AWS SES
```

**AWS Requirements:**
- Verified sender email address in AWS SES.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` configured in `.env`.

---

## 3. LangGraph Orchestration
The agent must define a stateful graph in `backend/app/agent/graph.py`.

### 3.1 Graph State Definition
```python
from typing import TypedDict, List

class DigestState(TypedDict):
    user_id: str
    reading_history: List[dict]
    echo_chamber_risk: float
    selected_articles: List[dict]
    contrarian_articles: List[dict]
    final_email_html: str
```

### 3.2 Node Definitions
1. **`RetrieveContextNode`**: Fetches the user's last 7 days of `reading_history` from CockroachDB.
2. **`AnalyzeBiasNode`**: Calculates the standard deviation of the `bias_score` of read articles. If the user only reads articles between `0.4` and `0.8` (Right-leaning), the `echo_chamber_risk` is HIGH.
3. **`CurateStandardNode`**: Performs a standard vector search (like Phase 5) to select 5 highly relevant articles.
4. **`CurateContrarianNode`**: *Conditional Node*. Only runs if `echo_chamber_risk > 0.7`. Re-runs the logic from Phase 8 on the user's top topic to find 1-2 opposing articles.
5. **`SynthesizeDigestNode`**: Passes the curated JSON lists to Groq (`llama3-8b-8192`). The prompt instructs the LLM to write a friendly, Markdown/HTML formatted email welcoming the user, summarizing their top news, and highlighting the "Perspective Check" section.

### 3.3 Graph Compilation
Compile the nodes into a linear flow, with the conditional edge routing to `CurateContrarianNode` if needed, converging at `SynthesizeDigestNode`.

---

## 4. AWS SES Integration
Create a utility (`backend/app/services/email.py`) using `boto3` to send the generated HTML payload to the user's email address.

**Implementation Requirement:**
```python
import boto3

def send_digest_email(to_email: str, html_content: str):
    client = boto3.client('ses', region_name='us-east-1')
    response = client.send_email(
        Source='digest@yourdomain.com',
        Destination={'ToAddresses': [to_email]},
        Message={
            'Subject': {'Data': 'Your Daily AmpliNews Digest'},
            'Body': {'Html': {'Data': html_content}}
        }
    )
    return response
```

---

## 5. AWS Lambda Handler
For the hackathon, we need to prove this can run serverlessly. Create a `backend/lambda_handler.py` entry point.

### Logic:
1. Query CockroachDB for a list of all active `user_id`s.
2. Loop through each user and invoke the LangGraph flow: `app.invoke({"user_id": user.id})`.
3. The graph handles the context retrieval, synthesis, and AWS SES email dispatch internally.

---

## 6. Validation & Verification Steps
Before considering Phase 9 complete, the executing agent MUST verify the following:
1. **Local Graph Test**: Invoke the LangGraph workflow locally in a Python script for a specific `user_id`. `print()` the final generated HTML string to ensure the LLM successfully wrote the email.
2. **Echo Chamber Trigger**: Manipulate a dummy user's reading history in CockroachDB to be 100% Left-leaning. Run the graph. Verify that the `CurateContrarianNode` was executed and opposing articles were injected into the state.
3. **SES Dispatch Test**: Run the full flow with a verified AWS SES email address and confirm the email actually arrives in your inbox with the correct HTML formatting.

---

## 7. Architectural Constraints to Remember
- **Lambda Timeouts**: A LangGraph workflow involving multiple LLM calls can take 10-20 seconds per user. If looping through 100 users, a single Lambda will time out. For the hackathon, looping sequentially is fine for a small demo. For production, the Lambda should fan-out (trigger individual SQS messages per user).
- **LLM Context Window**: Ensure you do not pass the entire full-text of 7 articles to Groq during the `SynthesizeDigestNode`. Pass only the titles, sources, and summaries to prevent exceeding the token limits.

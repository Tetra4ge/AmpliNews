# End-to-End User Flow: AmpliNews Agent

This document outlines the complete user journey and the invisible work performed by the AmpliNews agent behind the scenes.

## 1. IMMEDIATELY AFTER LOGIN (First Time)

### Step 1: Welcome & Interest Selection
- **User lands on dashboard.**
- **Agent says**: "Let's personalize your news. What interests you?"
- **User checks boxes**: Politics, Tech, Health, Sports, Business.
- **Optional**: User adds political preference (Left-leaning / Center / Right-leaning / Mixed).
- **Behind the scenes**: The Agent creates a `user_profile` in CockroachDB with initial `interest_embedding` vectors.

### Step 2: First News Feed Loads
- React frontend calls FastAPI: `GET /articles/feed?user_id=123`.
- FastAPI queries CockroachDB and finds articles matching the user's `interest_embedding`.
- The Agent retrieves ~50 articles from vector search.
- Frontend displays the top 10 articles featuring:
  - Headline
  - Source + credibility badge (e.g., ⭐⭐⭐⭐)
  - Bias indicator (🔴 Left / 🟡 Center / 🔵 Right)
  - Sentiment tag (breaking, analysis, opinion, etc.)
  - *"Why this? → You liked Politics & Tech"* (Agent reasoning)

---

## 2. READING ARTICLES (Ongoing)

When a user clicks an article, the frontend shows the title, source, bias, credibility, and content.

**Engagement Footer**:
- ❤️ Like
- 💬 Share
- ⚠️ Too biased
- 🔄 Show me the other side

### What's happening behind the scenes:
- Frontend tracks `scroll_depth`, `time_on_page`, and clicks.
- FastAPI logs these metrics to `reading_history` in CockroachDB.
- **Agent notes**: "User spent 4 mins on LEFT-leaning tech article."
- **Vector updated**: The user's `interest_embedding` slightly shifts toward tech.

### Scenario: User clicks "Show me the other side"
- Agent immediately queries CockroachDB and finds a RIGHT-leaning article on the exact same topic using vector similarity.
- Shows opposing perspective article below.
  - *Example*: User was reading "Tech Giants Should Be Regulated More" ➔ Other side shows "Tech Innovation Thrives Without Regulation".
- **Agent memory logs**: "User explored opposing view on tech regulation."

### Scenario: User clicks "Too biased"
- Feedback is stored in `reading_history`.
- **Agent notes**: "User rejected heavy-left article."
- **Next digest**: The Agent deprioritizes extreme-bias articles for this user.

---

## 3. DAILY DIGEST GENERATION (8 AM user's timezone)

Behind the scenes, driven by the LangGraph Agent and AWS Lambda:

1. **Trigger**: EventBridge triggers Lambda at 8 AM.
2. **Context Retrieval**: Agent retrieves user profile (interests, leaning) and the last 7 days of reading history.
   - *Pattern detected*: Reads 60% Tech, 30% Politics, 10% Health.
   - *Echo chamber risk*: 70% of reads from Center sources (⚠️ potential bubble).
3. **Generate Personalized Articles (70%)**:
   - Vector search finds 7 articles matching interests and patterns.
   - Ranked by relevance, recency, and credibility.
4. **Detect Echo Chamber**:
   - Analysis: "User reads only Center-leaning sources."
   - Action: Agent performs vector search for RIGHT-leaning articles on the "Politics" topic.
   - Selects the most credible contrarian option.
5. **Generate Full Digest**: Formats the digest into an email (sent via AWS SES) or JSON for the React dashboard. The digest explicitly highlights the **"Perspective Check"** and provides **"Reading Insights"**.

---

## 4. OVER TIME (Weekly/Monthly)

### Agent Learning
- **Day 7**: Notices user engaged with 3 right-leaning articles.
- **Day 14**: Slightly rebalances digest (e.g., 80% Center, 20% other perspectives).
- **Day 30**: If the user consistently explores opposing views, the `political_leaning` vector updates from "Center-Left" ➔ "Center". Confidence in preferences increases.

### User Dashboard Updates
- **Reading Stats**: "150 articles read, 60% match rate."
- **Bias Meter**: "You read 65% Center sources (was 80% last week) ✅ Less biased!"
- **Trust Score**: Agent predicts 87% you'll like tomorrow's digest.

### Weekly Insights
An automated weekly report showing most engaged topics, trending topics, echo chamber alerts, and a "Diversity Score".

---

## 5. AGENT'S INVISIBLE WORK (Summary)
✅ Tracks every article read (`reading_history`).
✅ Stores user interests as vectors (`user_profiles`).
✅ Remembers bias patterns (`agent_memory`).
✅ Detects echo chambers algorithmically.
✅ Finds semantically similar opposing articles via vector search in CockroachDB.
✅ Learns what resonated, what was ignored, and what surprised the user.
✅ No data is lost—everything persists safely in CockroachDB.

**The magic is that every click, read, and feedback loop teaches the agent. By month 2, the agent knows this user's media diet better than they know themselves.**

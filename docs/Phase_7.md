# Phase 7: Behavioral Tracking & Dynamic Memory

## 1. Phase Overview and Objectives
Phase 7 implements the continuous learning loop. The true power of the AmpliNews agent is its persistent memory in CockroachDB. Every interaction a user has with an article must subtly shift their `interest_embedding` vector, allowing the agent to curate better feeds over time and detect echo chambers.

**Objectives for the AI Agent executing this phase:**
- [ ] Build the frontend tracking logic to measure read duration and explicit feedback (Like / Too Biased).
- [ ] Create the `POST /api/articles/read` endpoint to log interactions to the `reading_history` table.
- [ ] Implement the math to dynamically shift the user's `interest_embedding` vector in CockroachDB based on their reading history.

---

## 2. Prerequisites & Environment Setup
Ensure Phases 1-6 are complete. The frontend must have the Reading View active, and the backend must be able to query both `user_profiles` and `articles`.

No new packages are strictly required, though `numpy` can be helpful for vector math on the backend.

---

## 3. Frontend Behavioral Tracking
The React application must passively and actively track engagement when a user is reading an article.

### 3.1 Passive Tracking (Read Duration)
- When the `ArticleDetail` component mounts, start a timer.
- When the component unmounts (or the user navigates away), capture the elapsed time in seconds.
- *Bonus*: Track maximum scroll depth percentage.

### 3.2 Active Feedback
- Implement the UI buttons: "❤️ Like" and "⚠️ Too Biased".
- Clicking these buttons should immediately trigger the tracking API call, bypassing the timer wait.

### 3.3 Sending the Data
The frontend triggers the API call to the backend:
```json
{
  "article_id": "uuid",
  "read_duration_seconds": 120,
  "liked": true,
  "rejected_biased": false
}
```

---

## 4. The Logging & Vector Shifting API

### API Specification:
- **Route**: `POST /api/articles/read`
- **Protection**: Requires JWT.

### 4.1 Logging the Event
1. Extract `user_id` from JWT.
2. Insert a new record into the `reading_history` table with the duration, article ID, and feedback flags.

### 4.2 Dynamic Vector Shifting (The Math)
This is the most critical agentic behavior. We must adjust the user's `interest_embedding` closer to (or further from) the read article's embedding.

**Implementation Requirement (Vector Math):**
1. Fetch the user's current `interest_embedding` ($U$) from `user_profiles`.
2. Fetch the article's `article_embedding` ($A$) from `articles`.
3. Determine a learning rate ($L$) based on engagement:
   - Read for > 60 seconds: $L = 0.05$
   - Clicked "Like": $L = 0.10$
   - Clicked "Too Biased": $L = -0.15$ (Shift *away* from this vector)
   - Bounced (< 5 seconds): $L = 0.0$ (Ignore)
4. Calculate the new vector: $U_{new} = U + (A - U) * L$
5. **CRITICAL**: Re-normalize $U_{new}$ to length 1.0 (if using cosine similarity, vector length must be normalized).
6. Update the `user_profiles.interest_embedding` with $U_{new}$.

---

## 5. Background Task Processing
Because vector math and database updates can take a few milliseconds, and we don't want to slow down the frontend's navigation, this shifting logic MUST happen in the background.

Use FastAPI's `BackgroundTasks`:
```python
from fastapi import BackgroundTasks

@router.post("/read")
def log_reading(payload: ReadPayload, background_tasks: BackgroundTasks, current_user = Depends(...)):
    # 1. Quickly insert into reading_history
    db.add(ReadingHistory(..., user_id=current_user.id))
    db.commit()
    
    # 2. Kick off vector shift asynchronously
    background_tasks.add_task(shift_user_vector, current_user.id, payload.article_id, payload.engagement_metrics)
    
    return {"status": "logged"}
```

---

## 6. Validation & Verification Steps
Before considering Phase 7 complete, the executing agent MUST verify the following:
1. **Frontend Trigger**: Open the React app, click an article, wait 10 seconds, and go back. Verify via the Network tab that the `/read` payload fired successfully.
2. **Database Logging**: Check the CockroachDB `reading_history` table. Verify the row was inserted with the correct duration.
3. **Vector Shift Verification**: 
   - Note the user's exact `interest_embedding` values in the database.
   - Send a `POST /api/articles/read` request with `liked: true`.
   - Check the database again. The `interest_embedding` float array MUST be slightly different.
4. **Rejection Math**: Send a request with `rejected_biased: true`. Ensure the math successfully moves the vector in the opposite direction (check for negative learning rate application).

---

## 7. Architectural Constraints to Remember
- CockroachDB handles vector updates cleanly, but ensure you are passing a standard Python `list` of floats to the SQLAlchemy model when updating, as the `pgvector` extension will handle the casting to the internal `VECTOR` type.

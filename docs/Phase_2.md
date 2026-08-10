# Phase 2: Authentication & User Management (Supabase + FastAPI)

## 1. Phase Overview and Objectives
Phase 2 focuses on establishing secure user identity management using **Supabase** and linking that identity to our persistent **CockroachDB** user profiles. 

In the AmpliNews architecture, Supabase acts strictly as the Identity Provider (IdP). It handles user signup, login, and JWT generation. The **FastAPI backend** is responsible for validating those JWTs and acting as the gateway to the CockroachDB memory layer. 

**Objectives for the AI Agent executing this phase:**
- [ ] Implement Supabase JWT validation as a dependency in FastAPI.
- [ ] Create the `POST /api/auth/sync` endpoint to mirror Supabase user data into CockroachDB.
- [ ] Implement the core onboarding logic: When a user selects their interests, the backend must generate an initial `interest_embedding` and store it in CockroachDB.
- [ ] Create the `GET /api/user/{user_id}` endpoint to retrieve the user's reading stats and bias metrics.

---

## 2. Prerequisites & Environment Setup
Ensure the following variables are present in `backend/.env`. The FastAPI backend needs the JWT secret to verify tokens independently without making round trips to Supabase.

**Required Environment Variables:**
```env
SUPABASE_URL="https://<your-project-id>.supabase.co"
SUPABASE_JWT_SECRET="<your-jwt-secret-from-supabase-dashboard>"
```

**Required Python Packages (`backend/requirements.txt`):**
```text
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.6.1
```

---

## 3. FastAPI JWT Validation Middleware
The executing agent must create a reusable FastAPI dependency (e.g., in `backend/app/core/security.py` or `backend/app/api/deps.py`) to protect routes.

### Validation Logic:
1. Extract the Bearer token from the `Authorization` header.
2. Use `python-jose` to decode and verify the JWT using the `SUPABASE_JWT_SECRET`.
3. The `aud` (audience) claim must be checked (usually `authenticated` in Supabase).
4. If valid, extract the `sub` (Subject / User ID) from the token.
5. If the token is invalid, expired, or missing, raise a `401 Unauthorized` `HTTPException`.

**Implementation Requirement:**
Every protected route in the application MUST use this dependency.
```python
@router.get("/protected-route")
def protected_route(current_user_id: str = Depends(get_current_user)):
    return {"user_id": current_user_id}
```

---

## 4. User Onboarding & Vector Initialization (`POST /api/auth/sync`)
When a user signs up on the frontend, the frontend will prompt them for their interests (e.g., "Politics, Tech") and their baseline political leaning (e.g., "Center-Left"). 

The frontend will then pass the JWT and these selections to the `sync` endpoint.

### API Specification:
- **Route**: `POST /api/auth/sync`
- **Protection**: Requires valid JWT.

**Request Payload:**
```json
{
  "selected_topics": ["Politics", "Technology", "Business"],
  "baseline_leaning": -0.5  // Represents Center-Left (-1.0 to 1.0)
}
```

### Agent Logic to Implement:
1. **Verify User**: Extract the `user_id` from the JWT.
2. **Check Existence**: Query CockroachDB (`user_profiles` table). If the user exists, return early.
3. **Generate Initial Vector**: 
   - The agent must construct a descriptive prompt representing the user's interests. Example: *"A reader interested in Politics, Technology, and Business."*
   - Call the embedding model (e.g., HuggingFace `all-MiniLM-L6-v2` or OpenAI/Groq embedding endpoint) to generate a 1536-dimensional vector for this text string.
4. **Persist to CockroachDB**:
   - Insert a new row into the `user_profiles` table.
   - Map the JWT `sub` to the `user_id` column.
   - Save the newly generated `interest_embedding`.
   - Save the `baseline_political_leaning`.

---

## 5. User Profile Retrieval (`GET /api/user/profile`)
The frontend dashboard needs to display the user's current metrics.

### API Specification:
- **Route**: `GET /api/user/profile`
- **Protection**: Requires valid JWT.

### Agent Logic to Implement:
1. Extract `user_id` from the JWT dependency.
2. Query CockroachDB for the `user_profiles` row.
3. Query the `reading_history` table to calculate simple aggregate stats:
   - Total articles read.
   - Most read topic.
4. Return the data to the frontend so it can render the "Bias Meter" and reading statistics.

---

## 6. Frontend Supabase Integration Context
While the agent is primarily building the backend in this phase, it should be aware of the frontend flow:
- The React app will use `@supabase/supabase-js`.
- The user will log in via Supabase UI.
- The React app retrieves the session: `supabase.auth.getSession()`.
- The React app attaches the `access_token` to all `fetch` requests targeting the FastAPI backend.

---

## 7. Validation & Verification Steps
Before considering Phase 2 complete, the executing agent MUST verify the following:
1. **JWT Rejection Test**: Make a request to a protected FastAPI endpoint without a token, or with an invalid token. It MUST return `401 Unauthorized`.
2. **JWT Acceptance Test**: Generate a valid Supabase JWT (using the secret) and ensure the FastAPI endpoint accepts it and correctly decodes the `user_id`.
3. **CockroachDB Insertion Test**: Hit the `/api/auth/sync` endpoint with a valid token and payload. Verify that a new row appears in the CockroachDB `user_profiles` table containing a valid 1536-dimensional vector array.
4. **Idempotency Check**: Hitting the `/sync` endpoint multiple times for the same user should NOT cause a primary key violation or overwrite their evolving vector.

---

## 8. Architectural Constraints to Remember
- **Do not store passwords**: AmpliNews does not store passwords or emails in CockroachDB. Supabase completely handles authentication credentials. We only store the UUID (`user_id`) to link our memory layers.
- **Vector Dimensions**: Ensure the embedding model used for initialization outputs exactly 1536 dimensions, as defined in the Phase 1 schema. If a different model is used (e.g., a 384-dimensional model), the SQLAlchemy model in Phase 1 MUST be updated.

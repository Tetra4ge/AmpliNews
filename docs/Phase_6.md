# Phase 6: Frontend Scaffold & Dashboard (React)

## 1. Phase Overview and Objectives
Phase 6 shifts focus from the backend infrastructure to the user-facing application. We will scaffold the React 19 frontend using Vite, implement Tailwind CSS for premium styling, and connect the UI to our FastAPI backend and Supabase authentication.

The goal is to build a modern, glassmorphic, dynamic dashboard that WOWs the hackathon judges instantly.

**Objectives for the AI Agent executing this phase:**
- [ ] Initialize the React + Vite + TypeScript project in the `frontend` directory.
- [ ] Configure Tailwind CSS and a premium color palette.
- [ ] Implement Supabase Auth UI (Login/Signup).
- [ ] Build the Onboarding Screen (Topic selection).
- [ ] Build the Main Dashboard (News Feed rendering).
- [ ] Ensure API calls are correctly attaching the Supabase JWT.

---

## 2. Prerequisites & Environment Setup
The agent must execute these commands inside the `frontend` directory.

**Required NPM Packages:**
```bash
npm install @supabase/supabase-js react-router-dom axios lucide-react clsx tailwind-merge framer-motion
```
*(Framer Motion is highly recommended for the micro-animations requested in the system prompt).*

**Environment Variables (`frontend/.env`):**
```env
VITE_SUPABASE_URL="<your-supabase-url>"
VITE_SUPABASE_ANON_KEY="<your-supabase-anon-key>"
VITE_API_DEV_URL="http://127.0.0.1:8000"
```

---

## 3. Core UI Architecture & Styling Rules

### 3.1 Design System (Critical Requirements)
As per the system instructions, a simple MVP look is UNACCEPTABLE. The UI must feel premium.
- **Theme**: Dark mode by default. Deep backgrounds (e.g., `#0F172A` or `#09090b`).
- **Typography**: Google Fonts `Inter` or `Outfit`.
- **Cards**: Glassmorphism effects for article cards (translucent backgrounds, subtle borders, backdrop blurs).
- **Feedback**: Hover effects on all clickable elements. Micro-animations when expanding articles.

### 3.2 Axios Interceptor
The agent MUST create an Axios instance (`frontend/src/api/client.ts`) that automatically intercepts requests and attaches the Supabase JWT token.

```typescript
import axios from 'axios';
import { supabase } from '../lib/supabase';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_DEV_URL,
});

apiClient.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data.session?.access_token) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

export default apiClient;
```

---

## 4. Feature Development

### 4.1 Onboarding Screen (`/onboarding`)
After a user signs up via Supabase, redirect them here if they haven't set their preferences.
- **UI**: A grid of visually appealing toggle buttons for topics (Politics, Tech, Health, Science). A slider for "Political Leaning".
- **Action**: On submit, POST to `apiClient.post('/api/auth/sync', payload)`.
- **Redirect**: Navigate to `/dashboard` on success.

### 4.2 Main Dashboard (`/dashboard`)
This is the core view.
- **Header**: "AmpliNews - Your Personalized Digest". Includes the user's current "Bias Meter" (a progress bar showing their left/center/right reading skew).
- **Feed Component**: Calls `GET /api/articles/feed` on mount.
- **Article Cards**: Render the list of articles. 
  - Show the title prominently.
  - Render colored badges for the Bias (🔴 Left, 🟡 Center, 🔵 Right).
  - Show the `match_percentage` in a glowing badge (e.g., `⭐ 95% Match`).

### 4.3 Reading View
When a user clicks a card, it should expand (or navigate to a detail view) to show the full article content.
- **Action**: Call `GET /api/articles/{id}` to fetch the full text.
- **Footer**: Implement the Engagement Footer with placeholders for "❤️ Like", "⚠️ Too biased", and "🔄 Show me the other side". (Wiring these up is Phase 7 & 8).

---

## 5. Validation & Verification Steps
Before considering Phase 6 complete, the executing agent MUST verify the following:
1. **Auth Flow**: Run `npm run dev`. Can you sign up for a new account via the UI, be redirected to the onboarding screen, and successfully hit the backend `/sync` endpoint?
2. **Token Injection**: Check the network tab in Chrome DevTools. Are requests to `/api/articles/feed` successfully carrying the `Authorization: Bearer <token>` header?
3. **Aesthetic Check**: Does the application look premium? Does it use a modern dark theme with distinct, non-default typography? 
4. **Rendering**: Does the dashboard successfully render the JSON payload constructed in Phase 5 into beautiful Article Cards?

---

## 6. Architectural Constraints to Remember
- **State Management**: For an app of this size, React Context or standard local state (`useState`, `useEffect`) is sufficient. Do not overengineer with Redux unless absolutely necessary.
- **Tailwind**: Stick to Tailwind CSS classes. Do not create separate `.css` files for component styling to ensure maintainability.

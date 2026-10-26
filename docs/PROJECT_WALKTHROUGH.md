# Mentor walkthrough and viva preparation

## 60-second explanation
RoamWise is a full-stack personalized travel itinerary planner. The React interface collects destination, dates, group size, budget, interests, travel style, pace, and accommodation preference. It sends those preferences to a FastAPI REST endpoint. The backend validates input with Pydantic and requests a day-by-day plan from Gemini when configured. If Gemini is unavailable or no key is set, a local rules-based engine creates a usable plan. Users can edit activities and save plans; the backend persists them in SQLite by default or Supabase when configured.

## Architecture
1. React/Vite UI → JSON REST requests (`/api/...`).
2. FastAPI → request validation, planner orchestration, error handling.
3. Planner → Gemini API (optional) or fallback rules engine.
4. Store adapter → SQLite (local) or Supabase Postgres (configured).
5. Pytest → health, generated itinerary structure, and input validation.

## Why use both generative AI and a fallback?
Generative AI makes itinerary language and suggestions more flexible. A deterministic fallback makes the project demonstrable without a paid key and protects the basic user flow from API downtime. Neither option should be presented as live booking inventory or verified current prices.

## Important viva questions
**Why FastAPI?** It is a Python ASGI framework with request validation, generated OpenAPI docs, async endpoint support, and a concise API implementation.

**What does Pydantic do?** It validates and parses request/response data; for example duration is constrained to 1–14 days and budget must be positive.

**What is REST?** A resource-oriented API convention using HTTP methods such as GET, POST, PUT, and DELETE.

**Why Supabase?** It offers managed PostgreSQL and can later provide authentication and row-level security. The demo uses a server-side service-role key only; production needs user auth and RLS policies.

**Is the model trained by this project?** No. Gemini is a pretrained generative model. The project engineers prompts and validates its output. The local fallback is a rules-based recommendation engine, not a trained ML model.

**How would you evaluate personalization?** Create test cases for solo/couple/group trips, vary budget/pace/interests, check itinerary day count and budget constraints, and conduct human relevance ratings. Track generation latency, malformed-output rate, cost, and user satisfaction.

**What are limitations?** Estimated costs are not live quotes; routes, opening hours, weather, and availability are not live-verified; authentication and per-user access control need completion before public production.

## Demo checklist
- Start backend and frontend in separate terminals.
- Open `/docs` and show API endpoints.
- Generate a solo, couple, and group plan with different interests and budgets.
- Edit an activity, print the itinerary, save it, refresh, reopen it, and delete a saved trip.
- Show health endpoint and run `pytest -q`.
- If demonstrating Gemini, configure the key in backend `.env` before starting the API; never show or commit the secret.

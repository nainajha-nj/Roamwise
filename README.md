# RoamWise — Personalized Travel Itinerary Planner

A full-stack internship project aligned to the provided project brief: React frontend, Python FastAPI REST API, Supabase-ready persistence, and Google Gemini-powered itinerary generation with a deterministic fallback engine.

## Features
- Responsive dashboard and trip planner
- Personalization by destination, dates/duration, budget, party type, interests, pace, and travel style
- Three supported scenarios: solo weekend getaway, couples' vacation, and group trip
- Day-by-day plan with morning/afternoon/evening activities, food ideas, logistics, and estimated costs
- Generate, edit activities, regenerate, save, open, and delete trips
- Budget breakdown and warning when estimated spend exceeds budget
- FastAPI validation, health endpoint, API docs, automated tests
- SQLite works out of the box; optional Supabase persistence adapter
- Optional Gemini API integration; no key needed for fallback generation

## Stack
- Frontend: React 18, Vite, plain CSS
- Backend: Python 3.11+, FastAPI, Pydantic
- Storage: SQLite by default; optional Supabase Postgres via Supabase REST API
- AI: Google Gemini REST API (optional), with a deterministic local fallback

## Run locally
### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; on macOS/Linux use: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Backend docs: http://localhost:8000/docs
Health check: http://localhost:8000/api/health

### 2. Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite (usually http://localhost:5173). The frontend proxies `/api` to `http://localhost:8000`.

## Configure AI and Supabase (optional)
Copy `backend/.env.example` to `backend/.env`.
- `GEMINI_API_KEY`: a Google AI Studio API key. Leave blank to use the local fallback engine.
- `GEMINI_MODEL`: defaults to `gemini-2.5-flash`.
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`: enable Supabase persistence. Create a `trips` table using `docs/supabase_schema.sql`. Keep the service-role key on the server only; never put it in frontend code or commit `.env`.
- If Supabase variables are absent, the app uses local SQLite at `backend/roamwise.db`.

### Supabase table
Run `docs/supabase_schema.sql` in the Supabase SQL editor. For a public production deployment, add proper Supabase Auth and Row Level Security policies before storing real user data. This demo API uses a server-side service-role key if configured and is intended for internship demonstration, not a public multi-tenant launch without auth.

## API overview
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service status and active providers |
| POST | `/api/itineraries/generate` | Generate a personalized itinerary |
| GET | `/api/trips` | List saved trips |
| POST | `/api/trips` | Save a trip |
| GET | `/api/trips/{trip_id}` | Read a saved trip |
| PUT | `/api/trips/{trip_id}` | Update a saved trip |
| DELETE | `/api/trips/{trip_id}` | Delete a saved trip |

Interactive API docs are available at `/docs`.

## Tests
```bash
cd backend
pip install -r requirements.txt
pytest -q
```

## Deployment notes
- Deploy the FastAPI backend to Render, Railway, or another Python ASGI host.
- Deploy the Vite frontend to Vercel/Netlify; set `VITE_API_BASE_URL` to the deployed backend URL if not using a same-origin reverse proxy.
- Set CORS origins using `CORS_ORIGINS` on the backend.
- Configure secrets only in the hosting provider's environment settings.
- For production: implement Supabase Auth, enforce RLS, add rate limits, validate AI output, add observability, and verify travel details against trusted live data sources. This app's prices and activity costs are estimates, not live quotes or booking availability.

## Important project integrity note
The AI model is a pretrained Gemini model when configured; this project does not claim to train a foundation model from scratch. The fallback is a transparent rules-based recommendation engine. This is appropriate for a practical internship project and makes the demo work even without an API key.

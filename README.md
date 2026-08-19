# ShootSignal

ShootSignal is a live, cited shoot-day intelligence agent for film crews. It uses the official
Parallel Search SDK at runtime to find current evidence, then uses Google ADK and Gemini to turn
that evidence into a concise Go / Caution / Reroute brief.

**Live app:** https://shootsignal-web.vercel.app

## Local setup

1. Copy `.env.example` to `.env.local`. For local development add `PARALLEL_API_KEY` and `GEMINI_API_KEY`; deployed Cloud Run uses `GOOGLE_CLOUD_PROJECT` and its service identity to call Vertex AI.
2. Install and run the web app: `npm install && npm run dev`.
3. In another terminal: `cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt && .venv/Scripts/uvicorn app.main:app --reload --port 8000`.
4. Open `http://localhost:3000` and generate a brief. The live demo must have `DEMO_FIXTURE=false`.

## Architecture

`Next.js UI -> FastAPI -> Parallel Search -> Gemini on Vertex AI / Google ADK -> citation-validated brief`

ShootSignal is planning support only. It does not grant permits or replace location, safety,
legal, weather, or emergency professionals.

## Contest compliance

`backend/app/main.py` imports and calls `parallel-web`, `google-adk`, and `google-genai` in its
runtime request path. This repository is licensed under Apache-2.0.

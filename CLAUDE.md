# Yorozuya

Max's personal job portal. Not public: only Max uses it. Two modes: **Curated** (live Greenhouse fetch
for a hand-picked list) and **Fresher** (DB-backed hunt for intern/new-grad roles). Backend rules are in
`backend/CLAUDE.md`.

## Layout
- `backend/`: FastAPI + SQLAlchemy 2 + Alembic, Python 3.14, managed with uv. Deployed on Railway.
- `frontend/`: React 19 + Vite + Tailwind v4. Deployed on Vercel (yorozuya.dizziedbliss.lol).
- `compose.yaml`: local Postgres (`127.0.0.1:5433`) and the API (`127.0.0.1:8000`, passphrase
  `local-dev`). Production DB is Supabase.

## Commands
- Start local Postgres: `docker compose up -d db`
- Full local stack: `docker compose up -d --build`
- Frontend: `cd frontend && npm ci && npm run dev -- --host 0.0.0.0`

## Rules
- Frontend code is TypeScript only (strict). No new `.js`/`.jsx`.
- Never commit `backend/.env` or `backend/.secrets`. `backend/.dockerignore` keeps them out of the image;
  keep it that way.

## Not built
- Fresher-mode sources, refresh worker, HR finder, Telegram ping, and the poster UI. The plan lives
  outside the repo.

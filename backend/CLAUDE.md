# Backend

## Commands (in order)
- Typecheck: `pyright` (fast, run first)
- Tests (need local Postgres: `docker compose up -d db` from the repo root): `uv run pytest -q`
  - one file: `uv run pytest -q tests/test_fresher_scorer.py`
  - one test: `uv run pytest -q -k senior`
- Lint and format: `uv run ruff check --fix . && uv run ruff format .`
- Dev server: `DATABASE_URL=postgresql://yorozuya:yorozuya@127.0.0.1:5433/yorozuya SITE_PASSPHRASE=local-dev uv run uvicorn main:app --reload`
- Migrate: `DATABASE_URL=… uv run alembic upgrade head`
- Refresh run (all sources, live): `DATABASE_URL=… uv run python -m worker.refresh`; skip some with
  `SKIP_SOURCES=jobspy:linkedin,jsearch` (JSearch has 200 requests/month: don't burn them testing).
- New migration: change `models.py`, then
  `DATABASE_URL=<empty db at head> uv run alembic revision --autogenerate --rev-id 000N -m "…"`, read it,
  and add RLS for any new table.

## Architecture
- `main.py` wires routers; `routers/` holds one file per area. `auth.py` has the passphrase dependency.
- `db.py`: engine and session from `DATABASE_URL` (any `postgres://` URL is fine; it adds the psycopg
  driver).
- `models.py` is the schema; `alembic/versions/` are the migrations. `tests/test_migrations.py` runs
  `alembic check`, so the two can't drift.
- `ranking/fresher.py` scores fresher jobs; **every weight is in `ranking/fresher_weights.py`**.
  `ranking/scores.py` is Curated's scorer: leave it alone.
- `pipeline/normalize.py`: salary in ₹ LPA (and from text like "₹6-8 LPA"), plus the cross-source dedupe key.
- `sources/`: one adapter per board, all `fetch(client, settings) -> SourceResult` (`sources/base.py`).
  `ats.py` (Greenhouse, Lever, Ashby, Workable, SmartRecruiters), `boards.py` (Remotive, RemoteOK,
  Himalayas, Arbeitnow), `jsearch.py`, `jobspy_source.py` (LinkedIn, Indeed, Naukri), `fx.py`.
- `pipeline/refresh.py` runs one refresh (fetch all → score → upsert → expire → log to
  `run_sources`); `worker/refresh.py` is its CLI, run every 6h by `.github/workflows/refresh.yml`.

## Rules
- Every route except `/health` and the legacy `/jobs` is locked: add routers with
  `dependencies=Locked` (from `auth.py`). The lock fails closed when `SITE_PASSPHRASE` is unset.
- Legacy `/jobs` is public only because the v1 frontend calls it without a passphrase. Remove it when
  the new frontend ships.
- Migrations are append-only: never edit one that has been applied anywhere. Every new table gets
  `ENABLE ROW LEVEL SECURITY` (Supabase serves `public` through its REST API; the migration test
  checks this).
- Operational values (thresholds, rates, the email template) go in the `settings` table. Secrets go in
  env only.
- Tests touch the network never: recorded fixtures in `tests/fixtures/` served by
  `tests/helpers.fake_client`, or patch the input list (see `tests/test_api.py`).
- A source that fails raises (`SourceBlocked` for 401/403/429, anything else for errors). Never return an
  empty result to hide a failure; the run logs it and carries on.
- Only a source that lists a company's *whole* board sets `RawJob.scope` / `complete_scopes`. Feeds and
  searches must not, or every job they didn't return this run would count as missing.
- The deployed worker uses Supabase's session pooler URL (IPv4). The direct `db.<ref>.supabase.co`
  host is IPv6-only and unreachable from GitHub runners.

## Gotchas
- JSONB through `postgresql.insert(...).values(value=...)` takes the Python dict. `json.dumps` first and it
  is encoded twice: you store a JSON *string*, not an object (bit migration 0002 once).

## Not built
- `/fresher/*`, HR finder, settings and logs APIs, Telegram pings.

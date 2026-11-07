# Backend

## Commands (in order)
- Typecheck: `pyright` (fast, run first)
- Tests (need local Postgres: `docker compose up -d db` from the repo root): `uv run pytest -q`
  - one file: `uv run pytest -q tests/test_fresher_scorer.py`
  - one test: `uv run pytest -q -k senior`
- Lint and format: `uv run ruff check --fix . && uv run ruff format .`
- Dev server: `DATABASE_URL=postgresql://yorozuya:yorozuya@127.0.0.1:5433/yorozuya SITE_PASSPHRASE=local-dev uv run uvicorn main:app --reload`
- Migrate: `DATABASE_URL=… uv run alembic upgrade head`
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
- `pipeline/normalize.py`: salary in ₹ LPA, plus the cross-source dedupe key.

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
- Tests touch the network never: fixtures, or patch the input list (see `tests/test_api.py`).

## Not built
- Source adapters, refresh worker, `/fresher/*`, HR finder, settings and logs APIs, Telegram.

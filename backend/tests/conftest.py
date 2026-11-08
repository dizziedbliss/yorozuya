import os

import psycopg
import pytest

# Local compose Postgres (127.0.0.1:5433). CI points TEST_DATABASE_URL at its service container.
ADMIN_URL = os.environ.get("TEST_ADMIN_URL", "postgresql://yorozuya:yorozuya@127.0.0.1:5433/yorozuya")
TEST_DB = "yorozuya_test"
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", f"postgresql+psycopg://yorozuya:yorozuya@127.0.0.1:5433/{TEST_DB}"
)


@pytest.fixture(scope="session")
def database_url() -> str:
    """A fresh, empty test database, recreated once per test session."""
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        conn.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
        conn.execute(f"CREATE DATABASE {TEST_DB}")
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def migrated_url(database_url) -> str:
    from alembic.config import Config

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")
    return database_url


@pytest.fixture
def db_engine(migrated_url):
    """The migrated test DB with every table emptied (alembic_version kept)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(migrated_url)
    with engine.begin() as conn:
        tables = (
            conn.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
        conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
    yield engine
    engine.dispose()


PASSPHRASE = "test-passphrase"


@pytest.fixture
def api(db_engine, migrated_url, monkeypatch):
    """A test client for the locked API, talking to the emptied test DB."""
    from fastapi.testclient import TestClient

    import main

    monkeypatch.setenv("DATABASE_URL", migrated_url)
    monkeypatch.setenv("SITE_PASSPHRASE", PASSPHRASE)
    client = TestClient(main.app)
    client.headers["X-Passphrase"] = PASSPHRASE
    return client


def add_job(engine, **fields) -> int:
    """Insert one job (plus its sources) straight into the DB; returns its id."""
    from datetime import UTC, datetime

    from sqlalchemy import insert

    from models import Job, JobSource

    sources = fields.pop("sources", ["greenhouse"])
    now = datetime(2026, 11, 8, 12, tzinfo=UTC)
    row = {
        "dedupe_key": fields.get("title", "t")
        + str(fields.get("company_name", "c"))
        + str(fields.get("location")),
        "company_name": "GitLab",
        "title": "DevOps Intern",
        "location": "Bengaluru, India",
        "apply_url": "https://job-boards.greenhouse.io/gitlab/jobs/1",
        "score": 100,
        "matched": ["devops", "intern"],
        "techs": ["docker"],
        "posted_at": now,
        "first_seen_at": now,
        "last_seen_at": now,
        "description": "Help run CI.",
    } | fields
    with engine.begin() as conn:
        job_id = conn.execute(insert(Job).values(**row).returning(Job.id)).scalar_one()
        for i, source in enumerate(sources):
            conn.execute(insert(JobSource).values(job_id=job_id, source=source, external_id=f"{job_id}-{i}"))
    return job_id

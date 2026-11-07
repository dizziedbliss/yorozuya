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

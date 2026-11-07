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

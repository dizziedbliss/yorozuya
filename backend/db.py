"""Database engine and sessions. DATABASE_URL comes from the environment (Supabase in prod)."""

import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def sqlalchemy_url(raw: str) -> str:
    """Supabase hands out postgres:// or postgresql:// URLs; SQLAlchemy needs the psycopg driver named."""
    for prefix in ("postgres://", "postgresql://"):
        if raw.startswith(prefix):
            return "postgresql+psycopg://" + raw.removeprefix(prefix)
    return raw


def database_url() -> str:
    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is not set")
    return sqlalchemy_url(raw)


@lru_cache(maxsize=4)
def engine_for(url: str) -> Engine:
    # pool_pre_ping: Supabase drops idle connections; check before handing one out.
    return create_engine(
        url, pool_pre_ping=True, pool_size=5, max_overflow=5, connect_args={"connect_timeout": 5}
    )


def get_engine() -> Engine:
    return engine_for(database_url())


def get_session() -> Iterator[Session]:
    with sessionmaker(get_engine())() as session:
        yield session

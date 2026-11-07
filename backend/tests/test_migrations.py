from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command


def _config(database_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def test_migrations_go_up_down_and_up_again_and_match_the_models(database_url):
    cfg = _config(database_url)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    # Raises if models.py and the migrations disagree about the schema.
    command.check(cfg)


def test_every_table_has_row_level_security_so_supabases_public_api_cannot_read_it(database_url):
    command.upgrade(_config(database_url), "head")

    engine = create_engine(database_url)
    with engine.connect() as conn:
        open_tables = (
            conn.execute(
                text(
                    "SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity"
                )
            )
            .scalars()
            .all()
        )
    engine.dispose()

    assert open_tables == []


def test_default_settings_are_seeded_as_json_objects(database_url):
    command.upgrade(_config(database_url), "head")

    engine = create_engine(database_url)
    with engine.connect() as conn:
        kinds = dict(conn.execute(text("SELECT key, jsonb_typeof(value) FROM settings")).all())
        queries = conn.execute(
            text("SELECT jsonb_array_length(value->'queries') FROM settings WHERE key = 'jsearch'")
        ).scalar()
    engine.dispose()

    assert kinds and set(kinds.values()) == {"object"}
    assert queries == 10

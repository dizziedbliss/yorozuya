"""Refresh run entry point: `uv run python -m worker.refresh [--trigger cron|manual]`.

Runs from GitHub Actions every 6h (see .github/workflows/refresh.yml) or by hand. Exits non-zero only
when the run itself can't happen (DB down); a broken source is logged in run_sources instead.
"""

import argparse
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy import Engine, insert, select

from db import get_engine
from models import RunSource, Setting
from notify.telegram import send_new_jobs
from pipeline.refresh import RunSummary, run_refresh
from sources.ats import FETCHERS, AtsSource
from sources.base import Source
from sources.boards import ArbeitnowSource, HimalayasSource, RemoteOkSource, RemotiveSource
from sources.fx import FxSource
from sources.jobspy_source import JobSpySource
from sources.jsearch import JSearchSource


def load_settings(engine: Engine) -> dict[str, Any]:
    with engine.connect() as conn:
        return {key: value for key, value in conn.execute(select(Setting.key, Setting.value)).all()}


def build_sources(settings: dict[str, Any]) -> list[Source]:
    sources: list[Source] = [AtsSource(ats) for ats in FETCHERS]
    sources += [JSearchSource(), RemotiveSource(), RemoteOkSource(), HimalayasSource(), ArbeitnowSource()]
    sources += [JobSpySource(site) for site in settings.get("jobspy", {}).get("sites", [])]
    sources.append(FxSource())
    skip = set(os.environ.get("SKIP_SOURCES", "").split(",")) - {""}
    return [s for s in sources if s.name not in skip]


def ping_telegram(engine: Engine, summary: RunSummary, settings: dict[str, Any]) -> str:
    """Send the run's best new jobs to Telegram and log the outcome as a `telegram` line in run_sources."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return "not configured"
    site_url = os.environ.get("SITE_URL", "https://yorozuya.dizziedbliss.lol")
    status, error = "ok", None
    try:
        with httpx.Client(timeout=20) as client:
            result = send_new_jobs(
                client, token, chat_id, summary.new_jobs, settings.get("notify", {}), site_url=site_url
            )
    except (RuntimeError, httpx.HTTPError) as exc:
        result, status, error = "failed", "error", f"{type(exc).__name__}: {exc}"
    with engine.begin() as conn:
        conn.execute(
            insert(RunSource).values(
                run_id=summary.run_id, source="telegram", status=status, error_text=error
            )
        )
    return result if status == "ok" else f"failed ({error})"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trigger", default="manual")
    args = parser.parse_args()
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    engine = get_engine()
    settings = load_settings(engine)
    sources = build_sources(settings)
    summary = run_refresh(engine, sources, settings, trigger=args.trigger, now=datetime.now(UTC))

    telegram = ping_telegram(engine, summary, settings)
    print(f"run {summary.run_id}: {len(summary.new_jobs)} new jobs, telegram: {telegram}")
    for name, status in sorted(summary.statuses.items()):
        print(f"  {status:8} {name}")
    for job in summary.new_jobs[:10]:
        print(f"  +{job['score']:4} {job['title']} @ {job['company']}")


if __name__ == "__main__":
    main()

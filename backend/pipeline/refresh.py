"""One refresh run: fetch every source at once, then score, dedupe, store, expire and log.

A source that breaks is logged (`blocked` / `error`) and the rest of the run carries on. Only a
source that listed a complete scope successfully can count a job as missed (see sources/base.py).
"""

import asyncio
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import Engine, case, func, literal_column, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from models import Company, Job, JobSource, RefreshRun, RunSource, Setting
from pipeline.discover import ats_from_url
from pipeline.normalize import dedupe_key, normalize_salary
from ranking.fresher import score_fresher
from sources.base import USER_AGENT, RawJob, Source, SourceBlocked, SourceResult

log = logging.getLogger(__name__)


@dataclass
class Outcome:
    source: Source
    status: str  # ok | blocked | error
    result: SourceResult = field(default_factory=SourceResult)
    error: str | None = None
    duration_ms: int = 0


@dataclass
class RunSummary:
    run_id: int
    statuses: dict[str, str]
    new_jobs: list[dict[str, Any]]


async def _fetch_one(
    source: Source, client: httpx.AsyncClient, settings: dict[str, Any], timeout: float
) -> Outcome:
    started = time.monotonic()
    try:
        result = await asyncio.wait_for(source.fetch(client, settings), timeout)
        outcome = Outcome(source, "ok", result)
    except SourceBlocked as exc:
        outcome = Outcome(source, "blocked", error=str(exc))
    except TimeoutError:
        outcome = Outcome(source, "error", error=f"timed out after {timeout:.0f}s")
    except (RuntimeError, httpx.HTTPError) as exc:  # expected trouble at a board: one line is enough
        log.warning("source %s failed: %s: %s", source.name, type(exc).__name__, exc)
        outcome = Outcome(source, "error", error=f"{type(exc).__name__}: {exc}")
    except Exception as exc:  # a bug in an adapter: keep the traceback, but never sink the run
        log.exception("source %s crashed", source.name)
        outcome = Outcome(source, "error", error=f"{type(exc).__name__}: {exc}")
    outcome.duration_ms = int((time.monotonic() - started) * 1000)
    return outcome


async def _fetch_all(
    sources: Sequence[Source], settings: dict[str, Any], client: httpx.AsyncClient | None
) -> list[Outcome]:
    timeout = float(settings.get("source_timeout_s", 300))
    if client is not None:
        return await asyncio.gather(*(_fetch_one(s, client, settings, timeout) for s in sources))
    async with httpx.AsyncClient(
        timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as own:
        return await asyncio.gather(*(_fetch_one(s, own, settings, timeout) for s in sources))


def _companies(conn: Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        select(Company.id, Company.name, Company.ats, Company.slug).where(
            Company.enabled.is_(True), Company.ats.is_not(None)
        )
    ).all()
    return [dict(row._mapping) for row in rows]


def _company_id(conn: Connection, raw: RawJob, by_board: dict[tuple[str, str], int]) -> int | None:
    """The job's company row: from its ATS scope, or discovered from its apply link."""
    board = None
    if raw.scope and ":" in raw.scope:
        ats, slug = raw.scope.split(":", 1)
        board = (ats, slug)
    board = board or ats_from_url(raw.apply_url)
    if board is None:
        return None
    if board not in by_board:
        conn.execute(
            insert(Company)
            .values(name=raw.company, ats=board[0], slug=board[1], origin="discovered")
            .on_conflict_do_nothing(index_elements=[Company.ats, Company.slug])
        )
        by_board[board] = conn.execute(
            select(Company.id).where(Company.ats == board[0], Company.slug == board[1])
        ).scalar_one()
    return by_board[board]


def _store(
    conn: Connection,
    raw: RawJob,
    settings: dict[str, Any],
    now: datetime,
    by_board: dict[tuple[str, str], int],
) -> dict[str, Any] | None:
    """Score and upsert one job. Returns it when it's new, None when it's known or filtered out."""
    scoring = settings.get("scoring", {})
    max_age = timedelta(days=int(scoring.get("max_age_days", 21)))
    if raw.posted_at is not None and now - raw.posted_at > max_age:
        return None
    scored = score_fresher(raw.title, raw.description, raw.location)
    if scored.dropped or scored.score < int(scoring.get("min_score", 30)):
        return None

    salary = normalize_salary(
        raw.salary_min,
        raw.salary_max,
        raw.salary_currency,
        raw.salary_period,
        settings.get("rates_to_inr", {}),
    )
    values = {
        "dedupe_key": dedupe_key(raw.company, raw.title, raw.location),
        "company_id": _company_id(conn, raw, by_board),
        "company_name": raw.company,
        "title": raw.title,
        "location": raw.location,
        "salary_min_lpa": salary[0] if salary else None,
        "salary_max_lpa": salary[1] if salary else None,
        "salary_estimated": raw.salary_estimated,
        "posted_at": raw.posted_at,
        "first_seen_at": now,
        "last_seen_at": now,
        "description": raw.description,
        "apply_url": raw.apply_url,
        "score": scored.score,
        "matched": scored.matched,
        "techs": scored.techs,
        "breakdown": [[label, points] for label, points in scored.breakdown],
    }
    stmt = insert(Job).values(**values)
    # Within one run (another source already touched this job) keep the better read of it;
    # on a later run the fresh score wins, so tightened rules actually lower old scores.
    same_run = Job.last_seen_at == now
    better = (stmt.excluded.score > Job.score) | ~same_run
    stmt = stmt.on_conflict_do_update(
        index_elements=[Job.dedupe_key],
        set_={
            "last_seen_at": now,
            "missed_runs": 0,
            "expired": False,
            "company_id": func.coalesce(Job.company_id, stmt.excluded.company_id),
            "salary_min_lpa": func.coalesce(stmt.excluded.salary_min_lpa, Job.salary_min_lpa),
            "salary_max_lpa": func.coalesce(stmt.excluded.salary_max_lpa, Job.salary_max_lpa),
            "posted_at": func.least(Job.posted_at, stmt.excluded.posted_at),
            "score": _pick(better, stmt.excluded.score, Job.score),
            "matched": _pick(better, stmt.excluded.matched, Job.matched),
            "techs": _pick(better, stmt.excluded.techs, Job.techs),
            "breakdown": _pick(better, stmt.excluded.breakdown, Job.breakdown),
            "description": _pick(
                (func.length(stmt.excluded.description) > func.coalesce(func.length(Job.description), 0))
                | ~same_run,
                stmt.excluded.description,
                Job.description,
            ),
        },
    ).returning(Job.id, literal_column("xmax = 0").label("inserted"))
    job_id, inserted = conn.execute(stmt).one()

    source_row = insert(JobSource).values(
        job_id=job_id,
        source=raw.source,
        external_id=raw.external_id,
        scope=raw.scope,
        url=raw.apply_url,
        seen_at=now,
    )
    conn.execute(
        source_row.on_conflict_do_update(
            index_elements=[JobSource.job_id, JobSource.source, JobSource.external_id],
            set_={"seen_at": now, "scope": source_row.excluded.scope},
        )
    )
    if not inserted:
        return None
    return {
        "id": job_id,
        "title": raw.title,
        "company": raw.company,
        "score": scored.score,
        "apply_url": raw.apply_url,
    }


def _pick(condition: Any, if_true: Any, otherwise: Any) -> Any:
    return case((condition, if_true), else_=otherwise)


def _expire(conn: Connection, complete_scopes: set[str], settings: dict[str, Any], now: datetime) -> None:
    expiry = settings.get("expiry", {})
    if complete_scopes:
        conn.execute(
            update(Job)
            .where(
                Job.last_seen_at < now,
                Job.id.in_(select(JobSource.job_id).where(JobSource.scope.in_(complete_scopes))),
            )
            .values(missed_runs=Job.missed_runs + 1)
        )
    stale_before = now - timedelta(days=int(expiry.get("stale_days", 21)))
    conn.execute(
        update(Job)
        .where(
            Job.expired.is_(False),
            (Job.missed_runs >= int(expiry.get("miss_limit", 2))) | (Job.last_seen_at < stale_before),
        )
        .values(expired=True)
    )


def _save_state(conn: Connection, key: str, patch: dict[str, Any], current: dict[str, Any]) -> None:
    value = {**current, **patch}
    stmt = insert(Setting).values(key=key, value=value)
    conn.execute(
        stmt.on_conflict_do_update(
            index_elements=[Setting.key],
            set_={"value": Setting.value.op("||")(stmt.excluded.value), "updated_at": func.now()},
        )
    )


def run_refresh(
    engine: Engine,
    sources: Sequence[Source],
    settings: dict[str, Any],
    *,
    trigger: str,
    now: datetime,
    client: httpx.AsyncClient | None = None,
) -> RunSummary:
    with engine.begin() as conn:
        run_id = conn.execute(
            insert(RefreshRun).values(trigger=trigger, started_at=now).returning(RefreshRun.id)
        ).scalar_one()
        companies = _companies(conn)

    source_settings = {**settings.get("boards", {}), **settings, "companies": companies}
    outcomes = asyncio.run(_fetch_all(sources, source_settings, client))

    new_jobs: list[dict[str, Any]] = []
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL lock_timeout = '30s'"))
        by_board = {(c["ats"], c["slug"]): c["id"] for c in companies}
        complete: set[str] = set()
        for outcome in outcomes:
            new_here = 0
            for raw in outcome.result.jobs:
                stored = _store(conn, raw, settings, now, by_board)
                if stored:
                    new_here += 1
                    new_jobs.append(stored)
            complete |= outcome.result.complete_scopes
            config_key = getattr(outcome.source, "config_key", None)
            if outcome.result.state and config_key:
                _save_state(conn, config_key, outcome.result.state, settings.get(config_key, {}))
            conn.execute(
                insert(RunSource).values(
                    run_id=run_id,
                    source=outcome.source.name,
                    status=outcome.status,
                    fetched=len(outcome.result.jobs),
                    new=new_here,
                    error_text=outcome.error or outcome.result.warning,
                    duration_ms=outcome.duration_ms,
                )
            )
        _expire(conn, complete, settings, now)
        conn.execute(update(RefreshRun).where(RefreshRun.id == run_id).values(finished_at=func.now()))

    return RunSummary(
        run_id=run_id,
        statuses={o.source.name: o.status for o in outcomes},
        new_jobs=sorted(new_jobs, key=lambda j: j["score"], reverse=True),
    )

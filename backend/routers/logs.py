"""Refresh run history: what each run fetched, per source, for the Logs page's tree rings."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import Locked
from db import get_session
from models import Job, RefreshRun, RunSource

router = APIRouter(prefix="/logs", tags=["logs"], dependencies=Locked)
SessionDep = Annotated[Session, Depends(get_session)]


class SourceLine(BaseModel):
    source: str
    status: str
    fetched: int
    new: int
    error_text: str | None
    duration_ms: int | None


class Run(BaseModel):
    id: int
    trigger: str
    started_at: datetime
    finished_at: datetime | None
    total_new: int
    sources: list[SourceLine]


class NewJob(BaseModel):
    id: int
    title: str
    company: str
    score: int


class RunDetail(Run):
    new_jobs: list[NewJob]


class RunList(BaseModel):
    runs: list[Run]


def _lines(session: Session, run_ids: list[int]) -> dict[int, list[SourceLine]]:
    by_run: dict[int, list[SourceLine]] = {run_id: [] for run_id in run_ids}
    rows = session.scalars(
        select(RunSource).where(RunSource.run_id.in_(run_ids)).order_by(RunSource.source)
    ).all()
    for row in rows:
        by_run[row.run_id].append(
            SourceLine(
                source=row.source,
                status=row.status,
                fetched=row.fetched,
                new=row.new,
                error_text=row.error_text,
                duration_ms=row.duration_ms,
            )
        )
    return by_run


def _run(run: RefreshRun, lines: list[SourceLine]) -> dict:
    return {
        "id": run.id,
        "trigger": run.trigger,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "total_new": sum(line.new for line in lines),
        "sources": lines,
    }


@router.get("/runs")
def list_runs(session: SessionDep, limit: Annotated[int, Query(ge=1, le=200)] = 40) -> RunList:
    runs = session.scalars(select(RefreshRun).order_by(RefreshRun.started_at.desc()).limit(limit)).all()
    lines = _lines(session, [run.id for run in runs])
    return RunList(runs=[Run(**_run(run, lines[run.id])) for run in runs])


@router.get("/runs/{run_id}")
def get_run(run_id: int, session: SessionDep) -> RunDetail:
    run = session.get(RefreshRun, run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    # A job is "new in this run" when it was first seen at the run's start (see pipeline/refresh.py).
    jobs = session.scalars(
        select(Job).where(Job.first_seen_at == run.started_at).order_by(Job.score.desc()).limit(100)
    ).all()
    return RunDetail(
        **_run(run, _lines(session, [run.id])[run.id]),
        new_jobs=[NewJob(id=j.id, title=j.title, company=j.company_name, score=j.score) for j in jobs],
    )

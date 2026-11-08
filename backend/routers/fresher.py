"""Fresher mode: the job list, one job, and Max's status on it."""

from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import ColumnElement, and_, func, literal, or_, select
from sqlalchemy.dialects.postgresql import ARRAY, insert
from sqlalchemy.orm import Session
from sqlalchemy.types import Text

from auth import Locked
from db import get_session
from hr.finder import Contact, find_contacts, http_client, mx_checker
from models import Company, HrContact, HrLookupMiss, Job, JobSource, JobStatus, JobStatusEvent, Setting

router = APIRouter(prefix="/fresher", tags=["fresher"], dependencies=Locked)

SessionDep = Annotated[Session, Depends(get_session)]
HttpDep = Annotated[httpx.Client, Depends(http_client)]
MxDep = Annotated[Callable[[str], bool], Depends(mx_checker)]
Status = Literal[
    "new", "applied", "emailed", "heard_back", "interview", "offer", "rejected", "ghosted", "skipped"
]
# Everything Max has acted on; these show on Receipts and never hide when a job is ghosted.
SENT: tuple[str, ...] = ("applied", "emailed", "heard_back", "interview", "offer", "rejected", "ghosted")
REPLIED = ("heard_back", "interview", "offer")
Where = Literal["bengaluru", "chennai", "india", "remote"]

WHERE_PATTERNS: dict[str, str] = {
    "bengaluru": "bengaluru|bangalore",
    "chennai": "chennai",
    "india": "india|bengaluru|bangalore|chennai",
    "remote": "remote|anywhere|worldwide",
}
KEEP_WHEN_EXPIRED = SENT


class JobCard(BaseModel):
    id: int
    title: str
    company: str
    location: str | None
    salary_min_lpa: float | None
    salary_max_lpa: float | None
    salary_estimated: bool
    posted_at: datetime | None
    first_seen_at: datetime
    score: int
    matched: list[str]
    techs: list[str]
    sources: list[str]
    status: Status
    expired: bool
    apply_url: str


class HrContactOut(BaseModel):
    email: str
    name: str | None
    origin: str
    confidence: int | None


class FindHrOut(BaseModel):
    status: Literal["found", "miss"]
    contacts: list[HrContactOut]
    cached: bool
    domain: str | None
    tried: list[str]
    hunter_error: str | None = None


class BreakdownPart(BaseModel):
    label: str
    points: int


class JobDetail(JobCard):
    description: str | None
    note: str | None
    hr_contacts: list[HrContactOut]
    breakdown: list[BreakdownPart]


class StatusEventOut(BaseModel):
    status: Status
    note: str | None
    at: datetime


class Receipt(JobCard):
    events: list[StatusEventOut]


class ReceiptStats(BaseModel):
    sent: int
    emailed: int
    replies: int
    interviews: int
    offers: int
    rejected: int
    ghosted: int


class ActivityDay(BaseModel):
    day: str
    applied: int


class Receipts(BaseModel):
    jobs: list[Receipt]
    stats: ReceiptStats
    activity: list[ActivityDay]


class JobList(BaseModel):
    total: int
    jobs: list[JobCard]


class StatusIn(BaseModel):
    status: Status
    note: str | None = Field(default=None, max_length=2000)


class StatusOut(BaseModel):
    job_id: int
    status: Status
    note: str | None
    updated_at: datetime


def _sources_subquery():
    return (
        select(JobSource.job_id, func.array_agg(func.distinct(JobSource.source)).label("sources"))
        .group_by(JobSource.job_id)
        .subquery()
    )


def _base_query():
    sources = _sources_subquery()
    status = func.coalesce(JobStatus.status, "new")
    query = (
        select(
            Job,
            status.label("status"),
            JobStatus.note,
            func.coalesce(sources.c.sources, literal([], ARRAY(Text))).label("sources"),
        )
        .outerjoin(JobStatus, JobStatus.job_id == Job.id)
        .outerjoin(sources, sources.c.job_id == Job.id)
    )
    return query, status, sources


def _card(job: Job, status: str, sources: list[str]) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company_name,
        "location": job.location,
        "salary_min_lpa": job.salary_min_lpa,
        "salary_max_lpa": job.salary_max_lpa,
        "salary_estimated": job.salary_estimated,
        "posted_at": job.posted_at,
        "first_seen_at": job.first_seen_at,
        "score": job.score,
        "matched": job.matched,
        "techs": job.techs,
        "sources": sorted(sources),
        "status": status,
        "expired": job.expired,
        "apply_url": job.apply_url,
    }


def _contacts_out(contacts: Iterable[HrContact | Contact]) -> list[HrContactOut]:
    """Stored contacts (HrContact rows) and fresh finds (finder Contacts) share one output shape."""
    return [
        HrContactOut(email=c.email, name=c.name, origin=c.origin, confidence=c.confidence) for c in contacts
    ]


@router.get("/jobs")
def list_jobs(
    session: SessionDep,
    where: Annotated[list[Where] | None, Query()] = None,
    role: Annotated[list[str] | None, Query(max_length=40)] = None,
    source: Annotated[str | None, Query(max_length=40)] = None,
    status: Annotated[list[Status] | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    salary_min: Annotated[float | None, Query(ge=0)] = None,
    salary_max: Annotated[float | None, Query(ge=0)] = None,
    include_no_salary: bool = True,
    include_expired: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JobList:
    query, status_col, sources = _base_query()
    filters: list[ColumnElement[bool]] = []

    if not include_expired:
        filters.append(or_(Job.expired.is_(False), status_col.in_(KEEP_WHEN_EXPIRED)))
    if where:
        filters.append(or_(*(Job.location.op("~*")(WHERE_PATTERNS[w]) for w in where)))
    if role:
        filters.append(Job.matched.op("&&")(literal(role, ARRAY(Text))))
    if source:
        filters.append(Job.id.in_(select(JobSource.job_id).where(JobSource.source == source)))
    if status:
        filters.append(status_col.in_(status))
    if q:
        pattern = f"%{q}%"
        filters.append(or_(Job.title.ilike(pattern), Job.company_name.ilike(pattern)))

    if salary_min is not None or salary_max is not None or not include_no_salary:
        has_pay: list[ColumnElement[bool]] = [
            or_(Job.salary_min_lpa.is_not(None), Job.salary_max_lpa.is_not(None))
        ]
        if salary_min is not None:
            has_pay.append(func.coalesce(Job.salary_max_lpa, Job.salary_min_lpa) >= salary_min)
        if salary_max is not None:
            has_pay.append(func.coalesce(Job.salary_min_lpa, Job.salary_max_lpa) <= salary_max)
        unpaid = and_(Job.salary_min_lpa.is_(None), Job.salary_max_lpa.is_(None))
        filters.append(or_(and_(*has_pay), unpaid) if include_no_salary else and_(*has_pay))

    query = query.where(*filters)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.execute(
        query.order_by(Job.score.desc(), func.coalesce(Job.posted_at, Job.first_seen_at).desc(), Job.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return JobList(
        total=total,
        jobs=[JobCard(**_card(job, row_status, row_sources)) for job, row_status, _note, row_sources in rows],
    )


@router.get("/jobs/{job_id}")
def get_job(job_id: int, session: SessionDep) -> JobDetail:
    query, _status, _sources = _base_query()
    row = session.execute(query.where(Job.id == job_id)).first()
    if row is None:
        raise HTTPException(404, "job not found")
    job, row_status, note, row_sources = row
    contacts = []
    if job.company_id is not None:
        contacts = session.scalars(
            select(HrContact)
            .where(HrContact.company_id == job.company_id)
            .order_by(HrContact.confidence.desc().nulls_last(), HrContact.email)
        ).all()
    return JobDetail(
        **_card(job, row_status, row_sources),
        description=job.description,
        note=note,
        hr_contacts=_contacts_out(contacts),
        breakdown=[BreakdownPart(label=label, points=points) for label, points in job.breakdown],
    )


@router.patch("/jobs/{job_id}/status")
def set_status(job_id: int, body: StatusIn, session: SessionDep) -> StatusOut:
    if session.get(Job, job_id) is None:
        raise HTTPException(404, "job not found")
    stmt = insert(JobStatus).values(job_id=job_id, status=body.status, note=body.note)
    row = session.execute(
        stmt.on_conflict_do_update(
            index_elements=[JobStatus.job_id],
            set_={"status": stmt.excluded.status, "note": stmt.excluded.note, "updated_at": func.now()},
        ).returning(JobStatus.job_id, JobStatus.status, JobStatus.note, JobStatus.updated_at)
    ).one()
    session.add(JobStatusEvent(job_id=job_id, status=body.status, note=body.note))
    session.commit()
    return StatusOut(job_id=row.job_id, status=row.status, note=row.note, updated_at=row.updated_at)


def _company_for(session: Session, job: Job) -> Company:
    """The job's company row, created (origin "manual") for feed jobs that don't have one yet."""
    if job.company_id is not None:
        company = session.get(Company, job.company_id)
        if company is not None:
            return company
    company = session.scalars(
        select(Company).where(func.lower(Company.name) == job.company_name.lower()).limit(1)
    ).first()
    if company is None:
        company = Company(name=job.company_name, origin="manual")
        session.add(company)
        session.flush()
    job.company_id = company.id
    return company


@router.post("/jobs/{job_id}/find-hr")
def find_hr(job_id: int, session: SessionDep, client: HttpDep, has_mx: MxDep) -> FindHrOut:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    company = _company_for(session, job)
    hr_settings: dict[str, Any] = (session.get(Setting, "hr") or Setting(key="hr", value={})).value

    cached = session.scalars(
        select(HrContact)
        .where(HrContact.company_id == company.id)
        .order_by(HrContact.confidence.desc().nulls_last(), HrContact.email)
    ).all()
    if cached:
        session.commit()
        return FindHrOut(
            status="found", contacts=_contacts_out(list(cached)), cached=True, domain=company.domain, tried=[]
        )
    miss = session.get(HrLookupMiss, company.id)
    retry_after = timedelta(days=int(hr_settings.get("retry_days", 30)))
    if miss is not None and datetime.now(UTC) - miss.tried_at < retry_after:
        session.commit()
        return FindHrOut(status="miss", contacts=[], cached=True, domain=company.domain, tried=[])

    outcome = find_contacts(
        company=job.company_name,
        description=job.description,
        apply_url=job.apply_url,
        known_domain=company.domain,
        settings=hr_settings,
        client=client,
        has_mx=has_mx,
    )
    if outcome.domain and not company.domain:
        company.domain = outcome.domain

    if outcome.contacts:
        for contact in outcome.contacts:
            session.execute(
                insert(HrContact)
                .values(
                    company_id=company.id,
                    email=contact.email,
                    name=contact.name,
                    origin=contact.origin,
                    confidence=contact.confidence,
                )
                .on_conflict_do_nothing(index_elements=[HrContact.company_id, HrContact.email])
            )
        if miss is not None:
            session.delete(miss)
    elif outcome.hunter_error is None:
        # A real miss. (When Hunter refused, don't remember it: the next click should try again.)
        stmt = insert(HrLookupMiss).values(company_id=company.id)
        session.execute(
            stmt.on_conflict_do_update(
                index_elements=[HrLookupMiss.company_id], set_={"tried_at": func.now()}
            )
        )
    session.commit()

    return FindHrOut(
        status="found" if outcome.contacts else "miss",
        contacts=_contacts_out(outcome.contacts),
        cached=False,
        domain=outcome.domain,
        tried=outcome.tried,
        hunter_error=outcome.hunter_error,
    )


@router.get("/receipts")
def receipts(session: SessionDep, days: Annotated[int, Query(ge=1, le=90)] = 14) -> Receipts:
    """Everything Max has sent, each with its status history, plus the numbers behind the Receipts page."""
    query, status_col, _sources = _base_query()
    rows = session.execute(query.where(status_col.in_(SENT))).all()
    ids = [job.id for job, *_ in rows]
    events: dict[int, list[JobStatusEvent]] = {job_id: [] for job_id in ids}
    for event in session.scalars(
        select(JobStatusEvent)
        .where(JobStatusEvent.job_id.in_(ids))
        .order_by(JobStatusEvent.at, JobStatusEvent.id)
    ):
        events[event.job_id].append(event)

    def reached(job_id: int, statuses: tuple[str, ...]) -> bool:
        return any(e.status in statuses for e in events[job_id])

    receipts_out = [
        Receipt(
            **_card(job, row_status, row_sources),
            events=[
                StatusEventOut.model_validate({"status": e.status, "note": e.note, "at": e.at})
                for e in events[job.id]
            ],
        )
        for job, row_status, _note, row_sources in rows
    ]
    receipts_out.sort(key=lambda r: r.events[-1].at if r.events else r.first_seen_at, reverse=True)

    current = {job.id: row_status for job, row_status, *_ in rows}
    stats = ReceiptStats(
        sent=len(ids),
        emailed=sum(reached(i, ("emailed",)) for i in ids),
        replies=sum(reached(i, REPLIED) for i in ids),
        interviews=sum(reached(i, ("interview", "offer")) for i in ids),
        offers=sum(current[i] == "offer" for i in ids),
        rejected=sum(current[i] == "rejected" for i in ids),
        ghosted=sum(current[i] == "ghosted" for i in ids),
    )
    today = datetime.now(UTC).date()
    applied_days = [
        e.at.astimezone(UTC).date() for evs in events.values() for e in evs if e.status == "applied"
    ]
    activity = [
        ActivityDay(day=(d := today - timedelta(days=back)).isoformat(), applied=applied_days.count(d))
        for back in range(days - 1, -1, -1)
    ]
    return Receipts(jobs=receipts_out, stats=stats, activity=activity)

"""Public ATS job boards (no key, no login): one AtsSource per ATS, covering every company on it."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from pipeline.text import html_to_text
from ranking.fresher import title_is_my_role
from sources.base import RawJob, SourceBlocked, SourceResult, from_iso, from_timestamp, raise_for_block

Company = dict[str, Any]
BoardFetcher = Callable[[httpx.AsyncClient, Company], Awaitable[list[RawJob]]]


async def _get_json(client: httpx.AsyncClient, url: str, **params: Any) -> Any:
    response = await client.get(url, params=params or None)
    raise_for_block(response)
    return response.json()


async def greenhouse(client: httpx.AsyncClient, company: Company) -> list[RawJob]:
    slug = company["slug"]
    data = await _get_json(client, f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", content="true")
    return [
        RawJob(
            source="greenhouse",
            external_id=str(job["id"]),
            title=job["title"],
            company=company["name"],
            apply_url=job["absolute_url"],
            location=(job.get("location") or {}).get("name"),
            description=html_to_text(job.get("content")),
            posted_at=from_iso(job.get("first_published") or job.get("updated_at")),
            scope=f"greenhouse:{slug}",
        )
        for job in data.get("jobs", [])
    ]


LEVER_INTERVALS = {
    "per-year-salary": "yearly",
    "per-month-salary": "monthly",
    "per-week-salary": "weekly",
    "per-day-wage": "daily",
    "per-hour-wage": "hourly",
}


def _remote(location: str | None, is_remote: bool | None) -> str | None:
    """Mark remote jobs so the location filter sees it, unless the text already says so."""
    if not is_remote:
        return location
    if location and "remote" in location.lower():
        return location
    return f"Remote ({location})" if location else "Remote"


async def lever(client: httpx.AsyncClient, company: Company) -> list[RawJob]:
    slug = company["slug"]
    data = await _get_json(client, f"https://api.lever.co/v0/postings/{slug}", mode="json")
    jobs = []
    for job in data:
        parts = [job.get("descriptionPlain") or ""]
        for section in job.get("lists") or []:
            parts.append(f"{section.get('text', '')}\n{html_to_text(section.get('content'))}")
        parts.append(job.get("additionalPlain") or "")
        salary = job.get("salaryRange") or {}
        categories = job.get("categories") or {}
        jobs.append(
            RawJob(
                source="lever",
                external_id=job["id"],
                title=job["text"],
                company=company["name"],
                apply_url=job["hostedUrl"],
                location=_remote(categories.get("location"), job.get("workplaceType") == "remote"),
                description="\n\n".join(p.strip() for p in parts if p.strip()),
                posted_at=from_timestamp(job.get("createdAt"), millis=True),
                salary_min=salary.get("min"),
                salary_max=salary.get("max"),
                salary_currency=salary.get("currency"),
                salary_period=LEVER_INTERVALS.get(salary.get("interval", "")),
                scope=f"lever:{slug}",
            )
        )
    return jobs


def _ashby_salary(compensation: dict[str, Any] | None) -> dict[str, Any]:
    for part in (compensation or {}).get("summaryComponents") or []:
        if part.get("compensationType") == "Salary":
            interval = (part.get("interval") or "").upper()
            period = {"1 YEAR": "yearly", "1 MONTH": "monthly", "1 HOUR": "hourly"}.get(interval)
            return {
                "salary_min": part.get("minValue"),
                "salary_max": part.get("maxValue"),
                "salary_currency": part.get("currencyCode"),
                "salary_period": period,
            }
    return {}


async def ashby(client: httpx.AsyncClient, company: Company) -> list[RawJob]:
    slug = company["slug"]
    data = await _get_json(
        client, f"https://api.ashbyhq.com/posting-api/job-board/{slug}", includeCompensation="true"
    )
    return [
        RawJob(
            source="ashby",
            external_id=job["id"],
            title=job["title"],
            company=company["name"],
            apply_url=job["jobUrl"],
            location=_remote(job.get("location"), job.get("isRemote")),
            description=job.get("descriptionPlain") or html_to_text(job.get("descriptionHtml")),
            posted_at=from_iso(job.get("publishedAt")),
            scope=f"ashby:{slug}",
            **_ashby_salary(job.get("compensation")),
        )
        for job in data.get("jobs", [])
        if job.get("isListed", True)
    ]


async def workable(client: httpx.AsyncClient, company: Company) -> list[RawJob]:
    slug = company["slug"]
    data = await _get_json(
        client, f"https://apply.workable.com/api/v1/widget/accounts/{slug}", details="true"
    )
    jobs = []
    for job in data.get("jobs", []):
        place = ", ".join(p for p in (job.get("city"), job.get("country")) if p) or None
        jobs.append(
            RawJob(
                source="workable",
                external_id=job["shortcode"],
                title=job["title"],
                company=company["name"],
                apply_url=job["url"],
                location=_remote(place, job.get("telecommuting")),
                description=html_to_text(job.get("description")),
                posted_at=from_iso(job.get("published_on")),
                scope=f"workable:{slug}",
            )
        )
    return jobs


async def smartrecruiters(client: httpx.AsyncClient, company: Company) -> list[RawJob]:
    slug = company["slug"]
    base = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    page_size, max_postings = 100, int(company.get("max_postings", 500))
    postings: list[dict[str, Any]] = []
    while len(postings) < max_postings:
        page = await _get_json(client, base, limit=page_size, offset=len(postings))
        postings.extend(page.get("content", []))
        if not page.get("content") or len(postings) >= page.get("totalFound", 0):
            break

    jobs = []
    for posting in postings:
        if not title_is_my_role(posting["name"]):
            continue
        detail = await _get_json(client, f"{base}/{posting['id']}")
        sections = (detail.get("jobAd") or {}).get("sections") or {}
        text = "\n\n".join(
            f"{section.get('title', '')}\n{html_to_text(section.get('text'))}"
            for key in ("jobDescription", "qualifications", "additionalInformation")
            if (section := sections.get(key))
        )
        place = posting.get("location") or {}
        jobs.append(
            RawJob(
                source="smartrecruiters",
                external_id=str(posting["id"]),
                title=posting["name"].strip(),
                company=company["name"],
                apply_url=detail.get("postingUrl")
                or f"https://jobs.smartrecruiters.com/{slug}/{posting['id']}",
                location=_remote(place.get("fullLocation"), place.get("remote")),
                description=text,
                posted_at=from_iso(posting.get("releasedDate")),
                scope=f"smartrecruiters:{slug}",
            )
        )
    return jobs


FETCHERS: dict[str, BoardFetcher] = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "workable": workable,
    "smartrecruiters": smartrecruiters,
}


def _describe(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return str(exc) or type(exc).__name__


class AtsSource:
    def __init__(self, ats: str):
        self.ats = ats
        self.name = ats
        self._fetch_board = FETCHERS[ats]

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        companies = [c for c in settings.get("companies", []) if c.get("ats") == self.ats]
        limit = asyncio.Semaphore(int(settings.get("ats_concurrency", 8)))

        async def one(company: Company) -> list[RawJob]:
            async with limit:
                return await self._fetch_board(client, company)

        outcomes = await asyncio.gather(*(one(c) for c in companies), return_exceptions=True)

        result = SourceResult()
        failures: list[tuple[str, BaseException]] = []
        for company, outcome in zip(companies, outcomes, strict=True):
            if isinstance(outcome, BaseException):
                failures.append((company["slug"], outcome))
                continue
            result.jobs.extend(outcome)
            result.complete_scopes.add(f"{self.ats}:{company['slug']}")

        if companies and len(failures) == len(companies):
            if all(isinstance(exc, SourceBlocked) for _, exc in failures):
                raise SourceBlocked(f"all {len(failures)} {self.ats} boards refused us")
            raise RuntimeError(
                f"all {len(failures)} {self.ats} boards failed, e.g. {_describe(failures[0][1])}"
            )
        if failures:
            noun = "board" if len(failures) == 1 else "boards"
            shown = ", ".join(f"{slug} ({_describe(exc)})" for slug, exc in failures[:5])
            more = f" and {len(failures) - 5} more" if len(failures) > 5 else ""
            result.warning = f"{len(failures)} {noun} failed: {shown}{more}"
        return result

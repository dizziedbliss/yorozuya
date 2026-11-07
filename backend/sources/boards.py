"""Free remote-job boards. They're feeds, not full company boards, so they never mark a job missed."""

from typing import Any

import httpx

from pipeline.normalize import parse_salary_text
from pipeline.text import html_to_text
from sources.base import RawJob, SourceResult, from_iso, from_timestamp, raise_for_block

HIMALAYAS_PERIODS = {"annual": "yearly", "yearly": "yearly", "monthly": "monthly", "hourly": "hourly"}


def _remote(where: str | None) -> str:
    where = (where or "").strip()
    if not where or where.lower() in ("worldwide", "anywhere", "remote"):
        return "Remote"
    return f"Remote ({where})"


async def _get_json(client: httpx.AsyncClient, url: str, **params: Any) -> Any:
    response = await client.get(url, params=params or None)
    raise_for_block(response)
    return response.json()


def _unique(jobs: list[RawJob]) -> list[RawJob]:
    seen: dict[str, RawJob] = {}
    for job in jobs:
        seen.setdefault(job.external_id, job)
    return list(seen.values())


class RemotiveSource:
    name = "remotive"

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        jobs: list[RawJob] = []
        for category in settings.get("remotive_categories", ["software-dev", "devops"]):
            data = await _get_json(client, "https://remotive.com/api/remote-jobs", category=category)
            for job in data.get("jobs", []):
                low, high, currency, period = parse_salary_text(job.get("salary")) or (None, None, None, None)
                jobs.append(
                    RawJob(
                        source=self.name,
                        external_id=str(job["id"]),
                        title=job["title"],
                        company=job["company_name"],
                        apply_url=job["url"],
                        location=_remote(job.get("candidate_required_location")),
                        description=html_to_text(job.get("description")),
                        posted_at=from_iso(job.get("publication_date")),
                        company_logo=job.get("company_logo"),
                        salary_min=low,
                        salary_max=high,
                        salary_currency=currency,
                        salary_period=period,
                    )
                )
        return SourceResult(jobs=_unique(jobs))


class RemoteOkSource:
    name = "remoteok"

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        data = await _get_json(client, "https://remoteok.com/api")
        jobs = [
            RawJob(
                source=self.name,
                external_id=str(job["id"]),
                title=job["position"],
                company=job["company"],
                apply_url=job.get("url") or job.get("apply_url"),
                location=_remote(job.get("location")),
                description=html_to_text(job.get("description")),
                posted_at=from_iso(job.get("date")),
                salary_min=job.get("salary_min") or None,
                salary_max=job.get("salary_max") or None,
                salary_currency="USD" if job.get("salary_min") or job.get("salary_max") else None,
                salary_period="yearly" if job.get("salary_min") or job.get("salary_max") else None,
                company_logo=job.get("company_logo") or None,
            )
            for job in data
            if "position" in job  # element 0 is a legal notice, not a job
        ]
        return SourceResult(jobs=jobs)


class HimalayasSource:
    name = "himalayas"

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        jobs: list[RawJob] = []
        page_size = 20
        for page in range(int(settings.get("himalayas_pages", 5))):
            data = await _get_json(
                client, "https://himalayas.app/jobs/api", limit=page_size, offset=page * page_size
            )
            batch = data.get("jobs", [])
            for job in batch:
                has_pay = job.get("minSalary") or job.get("maxSalary")
                jobs.append(
                    RawJob(
                        source=self.name,
                        external_id=job["guid"],
                        title=job["title"],
                        company=job["companyName"],
                        apply_url=job["applicationLink"],
                        location=_remote(", ".join(job.get("locationRestrictions") or [])),
                        description=html_to_text(job.get("description")),
                        posted_at=from_timestamp(job.get("pubDate")),
                        salary_min=job.get("minSalary") or None,
                        salary_max=job.get("maxSalary") or None,
                        salary_currency=job.get("currency") if has_pay else None,
                        salary_period=HIMALAYAS_PERIODS.get((job.get("salaryPeriod") or "").lower())
                        if has_pay
                        else None,
                        company_logo=job.get("companyLogo"),
                    )
                )
            if len(batch) < page_size:
                break
        return SourceResult(jobs=_unique(jobs))


class ArbeitnowSource:
    """Mostly on-site jobs in Germany; only its remote ones are any use to Max."""

    name = "arbeitnow"

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        jobs: list[RawJob] = []
        for page in range(1, int(settings.get("arbeitnow_pages", 3)) + 1):
            data = await _get_json(client, "https://www.arbeitnow.com/api/job-board-api", page=page)
            for job in data.get("data", []):
                if not job.get("remote"):
                    continue
                jobs.append(
                    RawJob(
                        source=self.name,
                        external_id=job["slug"],
                        title=job["title"],
                        company=job["company_name"],
                        apply_url=job["url"],
                        location=_remote(job.get("location")),
                        description=html_to_text(job.get("description")),
                        posted_at=from_timestamp(job.get("created_at")),
                    )
                )
            if not (data.get("links") or {}).get("next"):
                break
        return SourceResult(jobs=_unique(jobs))

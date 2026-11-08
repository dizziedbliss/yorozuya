"""JSearch (RapidAPI): Google for Jobs, which carries LinkedIn, Naukri, Indeed and company-site posts.

The free plan is 200 requests a month, so each run spends a small fixed budget, rotating through a
list of queries (`settings.jsearch`), and stops early when the monthly reserve is reached.
"""

import os
from typing import Any

import httpx

from sources.base import RawJob, SourceResult, from_iso, raise_for_block

URL = "https://jsearch.p.rapidapi.com/search-v2"
HOST = "jsearch.p.rapidapi.com"
PERIODS = {"YEAR": "yearly", "MONTH": "monthly", "WEEK": "weekly", "DAY": "daily", "HOUR": "hourly"}


def _job(raw: dict[str, Any], country: str) -> RawJob:
    location = raw.get("job_location") or ", ".join(
        p for p in (raw.get("job_city"), raw.get("job_state"), raw.get("job_country")) if p
    )
    if raw.get("job_is_remote") and "remote" not in (location or "").lower():
        location = f"Remote ({location})" if location else "Remote"
    has_pay = raw.get("job_min_salary") or raw.get("job_max_salary")
    return RawJob(
        source="jsearch",
        external_id=raw["job_id"],
        title=raw["job_title"],
        company=raw.get("employer_name") or "Unknown",
        apply_url=raw.get("job_apply_link") or raw.get("job_google_link") or "",
        location=location or None,
        description=raw.get("job_description") or "",
        posted_at=from_iso(raw.get("job_posted_at_datetime_utc")),
        salary_min=raw.get("job_min_salary"),
        salary_max=raw.get("job_max_salary"),
        # JSearch doesn't say the currency; it's the posting country's.
        salary_currency=("INR" if (raw.get("job_country") or country).upper() == "IN" else "USD")
        if has_pay
        else None,
        salary_period=PERIODS.get((raw.get("job_salary_period") or "").upper()) if has_pay else None,
        company_logo=raw.get("employer_logo"),
    )


class JSearchSource:
    name = "jsearch"

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult:
        key = os.environ.get("RAPIDAPI_KEY", "").strip()
        if not key:
            raise RuntimeError("RAPIDAPI_KEY is not set")
        config = settings.get("jsearch", {})
        queries: list[dict[str, str]] = config.get("queries", [])
        if not queries:
            return SourceResult(warning="no JSearch queries configured")
        index = int(config.get("query_index", 0))
        budget = int(config.get("requests_per_run", 1))
        reserve = int(config.get("min_remaining", 10))

        result = SourceResult()
        made = 0
        for _ in range(budget):
            query = queries[(index + made) % len(queries)]
            response = await client.get(
                URL,
                params={
                    "query": query["query"],
                    "country": query.get("country", "in"),
                    "num_pages": "1",
                    "date_posted": config.get("date_posted", "week"),
                },
                headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": HOST},
            )
            made += 1
            raise_for_block(response)
            for raw in (response.json().get("data") or {}).get("jobs", []):
                result.jobs.append(_job(raw, query.get("country", "in")))

            remaining = response.headers.get("x-ratelimit-requests-remaining")
            if remaining is not None and int(remaining) < reserve:
                result.warning = f"JSearch quota low ({remaining} left this month); stopped early"
                break

        result.state = {"query_index": index + made}
        return result

"""JobSpy (python-jobspy): scrapes LinkedIn, Indeed, Google Jobs and Naukri search pages, no login.

One source per board so each gets its own ok/blocked/error line in the logs. Each run uses the next
search in `settings.jobspy.searches` (rotating per board) and stays low-volume. JobSpy logs blocks
instead of raising, so we listen on the board's logger during the scrape.
"""

import asyncio
import json
import logging
import re
from collections.abc import Callable
from typing import Any

import httpx

from sources.base import RawJob, SourceBlocked, SourceResult, from_iso

BLOCK_SIGNS = re.compile(r"\b(429|403)\b|blocked|captcha|too many requests|rate limit", re.IGNORECASE)
# Indeed often gives only a state ("KA, India") or the country; we know which city we searched.
CITYLESS = re.compile(r"(?:[A-Z]{2}, )?India")


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        (self.errors if record.levelno >= logging.ERROR else self.warnings).append(record.getMessage())


def _default_scrape(**kwargs: Any) -> Any:
    from jobspy import scrape_jobs  # heavy import (pandas); only when really scraping

    return scrape_jobs(**kwargs)


def _location(raw: str | None, searched: str, remote: bool) -> str | None:
    loc = (raw or "").strip()
    if loc and CITYLESS.fullmatch(loc) and searched.lower() not in ("india", "remote"):
        loc = f"{searched} ({loc})"
    if remote and "remote" not in loc.lower():
        loc = f"Remote ({loc})" if loc else "Remote"
    return loc or None


class JobSpySource:
    config_key = "jobspy"

    def __init__(self, site: str, scrape: Callable[..., Any] = _default_scrape):
        self.site = site
        self.name = f"jobspy:{site}"
        self._scrape = scrape

    async def fetch(self, client: httpx.AsyncClient | None, settings: dict[str, Any]) -> SourceResult:
        config = settings.get("jobspy", {})
        searches: list[dict[str, Any]] = config.get("searches", [])
        if not searches:
            return SourceResult(warning="no JobSpy searches configured")
        index_key = f"index_{self.site}"
        index = int(config.get(index_key, 0))
        search = searches[index % len(searches)]
        term, where = search["term"], search.get("location", "India")

        capture = _Capture()
        logger = logging.getLogger(f"jobspy.{self.site}")
        logger.addHandler(capture)
        try:
            frame = await asyncio.to_thread(
                self._scrape,
                site_name=[self.site],
                search_term=term,
                google_search_term=f"{term} jobs in {where} since last week",
                location=where,
                is_remote=bool(search.get("remote", False)),
                country_indeed="india",
                results_wanted=int(config.get("results_wanted", 50)),
                hours_old=int(config.get("hours_old", 72)),
                description_format="markdown",
                verbose=1,
            )
        finally:
            logger.removeHandler(capture)

        rows = json.loads(frame.to_json(orient="records", date_format="iso")) if len(frame) else []
        if not rows and capture.errors:
            message = "; ".join(capture.errors[:3])
            if BLOCK_SIGNS.search(message):
                raise SourceBlocked(message)
            raise RuntimeError(message)

        jobs = [
            RawJob(
                source=self.name,
                external_id=str(row["id"]),
                title=row["title"],
                company=row.get("company") or "Unknown",
                apply_url=row.get("job_url_direct") or row["job_url"],
                location=_location(row.get("location"), where, bool(row.get("is_remote"))),
                description=row.get("description") or "",
                posted_at=from_iso(row.get("date_posted")),
                salary_min=row.get("min_amount"),
                salary_max=row.get("max_amount"),
                salary_currency=row.get("currency"),
                salary_period=row.get("interval"),
                company_logo=row.get("company_logo"),
            )
            for row in rows
            if row.get("title") and (row.get("job_url_direct") or row.get("job_url"))
        ]
        problems = capture.errors + capture.warnings
        return SourceResult(
            jobs=jobs,
            warning="; ".join(problems[:3]) if problems else None,
            state={index_key: index + 1},
        )

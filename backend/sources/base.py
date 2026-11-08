"""What every job source returns, and how a source reports trouble."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

USER_AGENT = "yorozuya-personal-job-search/1.0"


@dataclass
class RawJob:
    source: str  # "greenhouse", "jsearch", "jobspy:linkedin", ...
    external_id: str
    title: str
    company: str
    apply_url: str
    location: str | None = None
    description: str = ""
    posted_at: datetime | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    salary_estimated: bool = False
    # A board that lists *every* open job for this scope (one company's ATS board). A job missing
    # from a complete scope that fetched fine counts as a miss; search results never do.
    scope: str | None = None
    company_logo: str | None = None


@dataclass
class SourceResult:
    jobs: list[RawJob] = field(default_factory=list)
    # Scopes listed in full this run (see RawJob.scope). Only these can mark jobs as missed.
    complete_scopes: set[str] = field(default_factory=set)
    # Partial trouble that didn't stop the source ("2 boards failed: x, y").
    warning: str | None = None
    # Settings this source wants saved for next run (e.g. JSearch's next query index).
    state: dict[str, Any] | None = None


class SourceBlocked(Exception):
    """The board refused us (403/429, captcha). Logged as `blocked`, never retried in the same run."""


class Source(Protocol):
    name: str

    async def fetch(self, client: httpx.AsyncClient, settings: dict[str, Any]) -> SourceResult: ...


def raise_for_block(response: httpx.Response) -> None:
    if response.status_code in (401, 403, 429):
        raise SourceBlocked(f"HTTP {response.status_code} from {response.url.host}")
    response.raise_for_status()


def from_timestamp(value: float | int | None, *, millis: bool = False) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000 if millis else value, tz=UTC)


def from_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

"""Find someone to email about a job: the posting itself → Hunter → a guess at a domain that takes mail.

Every contact says where it came from ("posting", "hunter", "guess"). Hunter's free plan is 50
searches a month, so the caller caches results per company and only asks again after `retry_days`.
"""

import os
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import dns.exception
import dns.resolver
import httpx

from sources.base import USER_AGENT

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
HR_POSITION = re.compile(r"recruit|talent|\bhr\b|human resources|people (ops|partner)|hiring|campus", re.I)
HR_GENERIC = {"careers", "career", "jobs", "hr", "recruiting", "recruitment", "talent", "people", "hiring"}
# Hosts that belong to job boards and ATSes, never to the employer.
NOT_EMPLOYER = re.compile(
    r"greenhouse\.io|lever\.co|ashbyhq\.com|workable\.com|smartrecruiters\.com|myworkdayjobs\.com|"
    r"oraclecloud\.com|icims\.com|linkedin\.com|indeed\.com|naukri\.com|google\.com|remotive\.com|"
    r"remoteok\.com|himalayas\.app|arbeitnow\.com|glassdoor\.|wellfound\.com|instahyre\.com|jobleads\.com"
)
# Used when the `hr` settings row doesn't override them.
DEFAULT_SKIP_LOCALS = [
    "noreply",
    "no-reply",
    "donotreply",
    "privacy",
    "security",
    "abuse",
    "legal",
    "dpo",
    "gdpr",
]
DEFAULT_GUESS_LOCALS = ["careers", "hr", "recruiting", "talent", "jobs"]
TWO_PART_TLDS = {"co.in", "co.uk", "com.au", "com.br", "co.jp", "com.sg", "org.in", "net.in"}


@dataclass
class Contact:
    email: str
    origin: str  # posting | hunter | guess
    name: str | None = None
    confidence: int | None = None


@dataclass
class Outcome:
    contacts: list[Contact] = field(default_factory=list)
    domain: str | None = None
    tried: list[str] = field(default_factory=list)
    hunter_error: str | None = None


def http_client() -> Iterator[httpx.Client]:
    """FastAPI dependency; tests override it with a fake transport."""
    with httpx.Client(timeout=20, headers={"User-Agent": USER_AGENT}) as client:
        yield client


def _has_mx(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "MX", lifetime=5)
    except dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout:
        return False
    return True


def mx_checker() -> Callable[[str], bool]:
    """FastAPI dependency: does this domain accept email at all?"""
    return _has_mx


def emails_in_posting(text: str | None, skip_locals: list[str]) -> list[Contact]:
    found: dict[str, Contact] = {}
    for email in EMAIL.findall(text or ""):
        email = email.strip(".").lower()
        if email.split("@")[0] in skip_locals:
            continue
        found.setdefault(email, Contact(email=email, origin="posting", confidence=100))
    return list(found.values())


def registered_domain(host: str) -> str:
    parts = host.lower().removeprefix("www.").split(".")
    keep = 3 if ".".join(parts[-2:]) in TWO_PART_TLDS else 2
    return ".".join(parts[-keep:])


def employer_domain(apply_url: str | None, company: str) -> str | None:
    """careers.razorpay.com → razorpay.com, but only if it plausibly is the company's own site."""
    host = urlparse(apply_url or "").hostname or ""
    if not host or NOT_EMPLOYER.search(host):
        return None
    domain = registered_domain(host)
    words = [w for w in re.findall(r"[a-z0-9]+", company.lower()) if len(w) > 2]
    return domain if any(w in domain for w in words) else None


class HunterRefused(Exception):
    pass


def hunter(
    client: httpx.Client, key: str, company: str, domain: str | None
) -> tuple[list[Contact], str | None]:
    # Free plan returns 10 emails per search: ask for HR people only, or they get crowded out by engineers.
    params: dict[str, Any] = {"api_key": key, "limit": 10, "department": "hr"}
    params["domain" if domain else "company"] = domain or company
    response = client.get("https://api.hunter.io/v2/domain-search", params=params)
    if response.status_code in (401, 403, 429):
        raise HunterRefused(f"Hunter refused (HTTP {response.status_code}): out of searches this month?")
    response.raise_for_status()
    data = response.json().get("data") or {}
    contacts = []
    for person in data.get("emails") or []:
        local = person["value"].split("@")[0].lower()
        is_hr = (
            person.get("department") == "hr"
            or HR_POSITION.search(person.get("position") or "")
            or (person.get("type") == "generic" and local in HR_GENERIC)
        )
        if not is_hr:
            continue
        name = " ".join(p for p in (person.get("first_name"), person.get("last_name")) if p) or None
        contacts.append(
            Contact(
                email=person["value"].lower(), origin="hunter", name=name, confidence=person.get("confidence")
            )
        )
    contacts.sort(key=lambda c: c.confidence or 0, reverse=True)
    return contacts, data.get("domain")


def find_contacts(
    *,
    company: str,
    description: str | None,
    apply_url: str | None,
    known_domain: str | None,
    settings: dict[str, Any],
    client: httpx.Client,
    has_mx: Callable[[str], bool],
) -> Outcome:
    outcome = Outcome(domain=known_domain or employer_domain(apply_url, company))

    outcome.tried.append("posting")
    outcome.contacts = emails_in_posting(description, settings.get("skip_locals", DEFAULT_SKIP_LOCALS))
    if outcome.contacts:
        return outcome

    key = os.environ.get("HUNTER_API_KEY", "").strip()
    if key:
        outcome.tried.append("hunter")
        try:
            outcome.contacts, hunter_domain = hunter(client, key, company, outcome.domain)
            outcome.domain = outcome.domain or hunter_domain
        except HunterRefused as exc:
            outcome.hunter_error = str(exc)
        except httpx.HTTPError as exc:
            outcome.hunter_error = f"Hunter failed: {type(exc).__name__}"
        if outcome.contacts:
            return outcome

    outcome.tried.append("guess")
    if outcome.domain and has_mx(outcome.domain):
        outcome.contacts = [
            Contact(email=f"{local}@{outcome.domain}", origin="guess")
            for local in settings.get("guess_locals", DEFAULT_GUESS_LOCALS)
        ]
    return outcome

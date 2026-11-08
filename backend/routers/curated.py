"""Curated mode: live Greenhouse fetch for the hand-picked companies (v1 behaviour, unchanged)."""

import asyncio
import logging

from fastapi import APIRouter

from auth import Locked
from ranking.variables import companies
from services.greenhouse import get_greenhouse_jobs

log = logging.getLogger(__name__)

router = APIRouter(prefix="/curated", tags=["curated"], dependencies=Locked)


async def fetch_curated() -> list[dict]:
    results = await asyncio.gather(
        *(get_greenhouse_jobs(company) for company in companies), return_exceptions=True
    )
    all_jobs: list[dict] = []
    for company, result in zip(companies, results, strict=True):
        if isinstance(result, BaseException):
            log.warning("greenhouse fetch failed for %s: %r", company, result)
            continue
        all_jobs.extend(result)
    all_jobs.sort(key=lambda job: job["score"], reverse=True)
    return all_jobs


@router.get("/jobs")
async def curated_jobs() -> list[dict]:
    return await fetch_curated()

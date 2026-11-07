import os

import httpx
from dotenv import load_dotenv

from ranking.scores import calculate_score
from utils.helpers import timestamp_to_days_ago

load_dotenv()

LOGO_DEV_PUBLIC_KEY = os.getenv("LOGO_DEV_PUBLIC_KEY")


async def get_greenhouse_jobs(company):
    url = f"https://api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)

    response.raise_for_status()

    data = response.json()
    jobs = []

    for job in data.get("jobs", []):
        score = calculate_score((job.get("title") or "").lower(), (job.get("content") or "").lower())

        if score > 0:
            days = timestamp_to_days_ago(job.get("updated_at"))
            jobs.append(
                {
                    "title": job.get("title"),
                    "company": company,
                    "location": (job.get("location") or {}).get("name"),
                    "applicationLink": job.get("absolute_url"),
                    "logo": f"https://img.logo.dev/name/{company}?token={LOGO_DEV_PUBLIC_KEY}",
                    "updatedAt": f"{days} days ago" if days is not None else None,
                    "score": score,
                }
            )

    jobs.sort(key=lambda x: x["score"], reverse=True)

    return jobs

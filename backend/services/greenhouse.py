import httpx
from utils.helpers import  timestamp_to_days_ago
import os
from dotenv import load_dotenv
from ranking.scores import calculate_score

load_dotenv()

LOGO_DEV_PUBLIC_KEY = os.getenv('LOGO_DEV_PUBLIC_KEY')



async def get_greenhouse_jobs(company):
    print(f"Fetching {company}")
    url = f"https://api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
    
    response.raise_for_status()       
       
    data = response.json()
    print(f"Fetched {company}")
    jobs = []

    for job in data.get("jobs",[]):
        
        score = 0
        
        score = calculate_score(job.get("title", "").lower(), job.get("content", "").lower())
        
        if score > 0:
            jobs.append({
                "title": job.get("title"),
                "company": company,
                "location": job.get("location", {}).get("name"),
                "applicationLink": job.get("absolute_url"),
                "logo":  f"https://img.logo.dev/name/{company}?token={LOGO_DEV_PUBLIC_KEY}",
                "updatedAt": f"{timestamp_to_days_ago(job.get('updated_at'))} days ago",
                "score": score
            })
        
    jobs.sort(key=lambda x: x["score"], reverse=True)

    return jobs

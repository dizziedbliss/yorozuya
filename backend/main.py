from fastapi import FastAPI, requests
from fastapi.middleware.cors import CORSMiddleware
from greenhouse import get_greenhouse_jobs
from variables import companies

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

companies = companies

@app.get("/jobs")
async def get_jobs():
    all_jobs = []

    try:
        for company in companies:
            jobs = get_greenhouse_jobs(company)
            all_jobs.extend(jobs)

    except Exception as e:
        print(f"Error fetching jobs from {companies}: {e}")

    return all_jobs
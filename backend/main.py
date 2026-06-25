import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.greenhouse import get_greenhouse_jobs
from ranking.variables import companies


app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://yorozuya.dizziedbliss.dev"
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

    tasks = [    
            get_greenhouse_jobs(company)
            for company in companies        
    ]

    results = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )

    all_jobs = []

    for result in results:

        if isinstance(result, Exception):
            print(result)
            continue

        all_jobs.extend(result)
        
        all_jobs.sort(key=lambda x: x["score"], reverse=True)

    return all_jobs

@app.get("/ping")
async def ping():
    return {"status": "alive"}
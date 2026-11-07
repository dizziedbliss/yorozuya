from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import curated, health

app = FastAPI(title="Yorozuya")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://yorozuya.dizziedbliss.lol",
    "https://yorozuya-rho.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(curated.router)


@app.get("/jobs", tags=["legacy"])
async def legacy_jobs() -> list[dict]:
    """v1 route the live frontend still calls. Public until the stage 4 frontend sends the passphrase."""
    return await curated.fetch_curated()

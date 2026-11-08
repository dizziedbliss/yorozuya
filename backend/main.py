from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import curated, fresher, health, logs, settings

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
app.include_router(fresher.router)
app.include_router(settings.router)
app.include_router(logs.router)

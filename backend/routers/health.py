import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db import get_engine

log = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> JSONResponse:
    """Public on purpose (Railway's health check can't send a passphrase). Says nothing secret."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except (SQLAlchemyError, RuntimeError) as exc:
        log.error("health: database unreachable: %s", type(exc).__name__)
        return JSONResponse({"status": "degraded", "db": "down"}, status_code=503)
    return JSONResponse({"status": "ok", "db": "up"})

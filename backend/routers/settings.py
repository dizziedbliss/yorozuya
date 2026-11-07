"""Operational settings (thresholds, searches, the Gmail template). Secrets never live here."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from auth import Locked
from db import get_session
from models import Setting

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=Locked)
SessionDep = Annotated[Session, Depends(get_session)]

EDITABLE = {
    "scoring",
    "expiry",
    "rates_to_inr",
    "boards",
    "jsearch",
    "jobspy",
    "notify",
    "hr",
    "email_template",
}


class EmailTemplate(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=10_000)


@router.get("")
def read_settings(session: SessionDep) -> dict[str, dict[str, Any]]:
    return {key: value for key, value in session.execute(select(Setting.key, Setting.value))}


@router.put("/{key}")
def write_setting(key: str, value: Annotated[dict[str, Any], Body()], session: SessionDep) -> dict[str, Any]:
    if key not in EDITABLE:
        raise HTTPException(404, f"no editable setting called {key!r}")
    if key == "email_template":
        try:
            value = EmailTemplate.model_validate(value).model_dump()
        except ValidationError as exc:
            raise HTTPException(422, exc.errors(include_url=False, include_input=False)) from exc
    stmt = insert(Setting).values(key=key, value=value)
    session.execute(
        stmt.on_conflict_do_update(
            index_elements=[Setting.key], set_={"value": stmt.excluded.value, "updated_at": func.now()}
        )
    )
    session.commit()
    return {"key": key, "value": value}

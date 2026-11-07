"""The fresher-mode schema. Changes go through a new Alembic migration; `alembic check` in the tests
fails if this file and the migrations disagree."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NOW = func.now()


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: JSONB,
        list[str]: ARRAY(Text),
        datetime: DateTime(timezone=True),
    }


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("ats", "slug"),
        CheckConstraint("origin IN ('seed', 'discovered', 'manual')", name="companies_origin_check"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(Text)
    ats: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(Text, server_default="seed")
    enabled: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=NOW)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("jobs_feed_idx", "expired", "score"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dedupe_key: Mapped[str] = mapped_column(Text, unique=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    company_name: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    remote_type: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str | None] = mapped_column(Text)
    salary_min_lpa: Mapped[float | None] = mapped_column(Float)
    salary_max_lpa: Mapped[float | None] = mapped_column(Float)
    salary_estimated: Mapped[bool] = mapped_column(server_default="false")
    posted_at: Mapped[datetime | None]
    first_seen_at: Mapped[datetime] = mapped_column(server_default=NOW)
    last_seen_at: Mapped[datetime] = mapped_column(server_default=NOW)
    missed_runs: Mapped[int] = mapped_column(Integer, server_default="0")
    expired: Mapped[bool] = mapped_column(server_default="false")
    description: Mapped[str | None] = mapped_column(Text)
    apply_url: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer, server_default="0")
    matched: Mapped[list[str]] = mapped_column(server_default="{}")
    techs: Mapped[list[str]] = mapped_column(server_default="{}")


class JobSource(Base):
    __tablename__ = "job_sources"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    external_id: Mapped[str] = mapped_column(Text, primary_key=True)
    url: Mapped[str | None] = mapped_column(Text)
    seen_at: Mapped[datetime] = mapped_column(server_default=NOW)


class JobStatus(Base):
    __tablename__ = "job_status"
    __table_args__ = (
        CheckConstraint("status IN ('new', 'applied', 'emailed', 'skipped')", name="job_status_status_check"),
    )

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(Text, server_default="new")
    note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(server_default=NOW)


class HrContact(Base):
    __tablename__ = "hr_contacts"
    __table_args__ = (UniqueConstraint("company_id", "email"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(Text)
    confidence: Mapped[int | None] = mapped_column(Integer)
    found_at: Mapped[datetime] = mapped_column(server_default=NOW)


class HrLookupMiss(Base):
    __tablename__ = "hr_lookup_misses"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    tried_at: Mapped[datetime] = mapped_column(server_default=NOW)


class RefreshRun(Base):
    __tablename__ = "refresh_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trigger: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(server_default=NOW)
    finished_at: Mapped[datetime | None]


class RunSource(Base):
    __tablename__ = "run_sources"
    __table_args__ = (
        CheckConstraint("status IN ('ok', 'blocked', 'error')", name="run_sources_status_check"),
    )

    run_id: Mapped[int] = mapped_column(ForeignKey("refresh_runs.id", ondelete="CASCADE"), primary_key=True)
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    status: Mapped[str] = mapped_column(Text)
    fetched: Mapped[int] = mapped_column(Integer, server_default="0")
    new: Mapped[int] = mapped_column(Integer, server_default="0")
    error_text: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class Setting(Base):
    """Operational knobs only (thresholds, rates, the email template). Secrets live in env."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict[str, Any]]
    updated_at: Mapped[datetime] = mapped_column(server_default=NOW)

"""hr finder and email template settings

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-08 03:11:32.923034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Pass dicts straight to JSONB (never json.dumps: see backend/CLAUDE.md gotchas).
DEFAULTS = {
    "hr": {
        "retry_days": 30,
        "guess_locals": ["careers", "hr", "recruiting", "talent", "jobs"],
        "skip_locals": ["noreply", "no-reply", "donotreply", "privacy", "security", "abuse", "legal", "dpo", "gdpr"],
    },
    "email_template": {
        "subject": "{role} application: Adithya (DevOps / Cloud, 2027 grad)",
        "body": "Hi {hr_name},\n\nI came across the {role} opening at {company} ({job_link}) and wanted to reach out directly.\n\nI'm Adithya, a CSE (AI & ML) student at Malnad College of Engineering, graduating in 2027. I work on the DevOps and fullstack side: CI/CD with GitHub Actions, secrets with SOPS, Docker, and self-hosted Linux/Proxmox infrastructure. My main project, SkillIssues (Go, React, PostgreSQL, Docker), is a live open-source platform that surfaces GitHub issues to work on; it was a finalist at Hack Summit A'26.\n\nI'd love to be considered for this role. My resume is attached, and more of my work is at github.com/dizziedbliss and dizziedbliss.lol.\n\nThanks for your time,\nAdithya\nlinkedin.com/in/dizziedbliss",
    },
}

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    settings = sa.table("settings", sa.column("key", sa.Text), sa.column("value", postgresql.JSONB))
    for key, value in DEFAULTS.items():
        op.execute(
            postgresql.insert(settings).values(key=key, value=value).on_conflict_do_nothing(index_elements=["key"])
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DELETE FROM settings WHERE key = ANY(:keys)").bindparams(keys=list(DEFAULTS)))

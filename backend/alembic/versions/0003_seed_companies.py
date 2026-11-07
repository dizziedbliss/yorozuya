"""seed companies

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-08 02:46:54.095812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Verified on 2026-11-08: every board answered with at least one job. Discovery adds more over time.
SEED = [
    ('Airbyte', 'ashby', 'airbyte'),
    ('Anthropic', 'greenhouse', 'anthropic'),
    ('Atlan', 'ashby', 'atlan'),
    ('Brex', 'greenhouse', 'brex'),
    ('Buffer', 'ashby', 'buffer'),
    ('CRED', 'lever', 'cred'),
    ('Canonical', 'greenhouse', 'canonical'),
    ('CircleCI', 'greenhouse', 'circleci'),
    ('Clerk', 'ashby', 'clerk'),
    ('Cloudflare', 'greenhouse', 'cloudflare'),
    ('Cockroach Labs', 'greenhouse', 'cockroachlabs'),
    ('Coinbase', 'greenhouse', 'coinbase'),
    ('Databricks', 'greenhouse', 'databricks'),
    ('Datadog', 'greenhouse', 'datadog'),
    ('DevRev', 'greenhouse', 'devrev'),
    ('Discord', 'greenhouse', 'discord'),
    ('Docker', 'ashby', 'docker'),
    ('Dropbox', 'greenhouse', 'dropbox'),
    ('Druva', 'greenhouse', 'druva'),
    ('Duolingo', 'greenhouse', 'duolingo'),
    ('Elastic', 'greenhouse', 'elastic'),
    ('Fastly', 'greenhouse', 'fastly'),
    ('Fi Money', 'lever', 'fi'),
    ('Figma', 'greenhouse', 'figma'),
    ('Fly.io', 'lever', 'fly'),
    ('GitLab', 'greenhouse', 'gitlab'),
    ('Glean', 'greenhouse', 'gleanwork'),
    ('Grafana Labs', 'greenhouse', 'grafanalabs'),
    ('Groww', 'greenhouse', 'groww'),
    ('Harness', 'greenhouse', 'harnessinc'),
    ('Hightouch', 'ashby', 'hightouch'),
    ('InMobi', 'greenhouse', 'inmobi'),
    ('JetBrains', 'greenhouse', 'jetbrains'),
    ('Kong', 'ashby', 'kong'),
    ('Linear', 'ashby', 'linear'),
    ('Meesho', 'lever', 'meesho'),
    ('Mindtickle', 'lever', 'mindtickle'),
    ('MongoDB', 'greenhouse', 'mongodb'),
    ('Mozilla', 'greenhouse', 'mozilla'),
    ('Neon', 'lever', 'neon'),
    ('Netlify', 'greenhouse', 'netlify'),
    ('New Relic', 'greenhouse', 'newrelic'),
    ('Notion', 'ashby', 'notion'),
    ('Observe.AI', 'greenhouse', 'observeai'),
    ('Okta', 'greenhouse', 'okta'),
    ('OpenAI', 'ashby', 'openai'),
    ('PagerDuty', 'greenhouse', 'pagerduty'),
    ('Palantir', 'lever', 'palantir'),
    ('Paytm', 'lever', 'paytm'),
    ('Pinterest', 'greenhouse', 'pinterest'),
    ('Plaid', 'ashby', 'plaid'),
    ('PlanetScale', 'greenhouse', 'planetscale'),
    ('PostHog', 'ashby', 'posthog'),
    ('Railway', 'ashby', 'railway'),
    ('Ramp', 'ashby', 'ramp'),
    ('Razorpay', 'greenhouse', 'razorpaysoftwareprivatelimited'),
    ('Reddit', 'greenhouse', 'reddit'),
    ('Redis', 'ashby', 'redis'),
    ('Remote.com', 'greenhouse', 'remote'),
    ('Render', 'ashby', 'render'),
    ('Replit', 'ashby', 'replit'),
    ('Resend', 'ashby', 'resend'),
    ('Robinhood', 'greenhouse', 'robinhood'),
    ('Roblox', 'greenhouse', 'roblox'),
    ('Rubrik', 'greenhouse', 'rubrik'),
    ('Sarvam AI', 'ashby', 'sarvam'),
    ('Scale AI', 'greenhouse', 'scaleai'),
    ('Sentry', 'ashby', 'sentry'),
    ('Slice', 'greenhouse', 'slice'),
    ('Snyk', 'ashby', 'snyk'),
    ('Stripe', 'greenhouse', 'stripe'),
    ('Supabase', 'ashby', 'supabase'),
    ('Tailscale', 'greenhouse', 'tailscale'),
    ('Temporal', 'ashby', 'temporal'),
    ('Timescale', 'ashby', 'tigerdata'),
    ('Toptal', 'lever', 'toptal'),
    ('Twilio', 'greenhouse', 'twilio'),
    ('Vanta', 'ashby', 'vanta'),
    ('Vercel', 'greenhouse', 'vercel'),
    ('Warp', 'ashby', 'warp'),
    ('Wiz', 'greenhouse', 'wizinc'),
    ('Zapier', 'ashby', 'zapier'),
    ('Zeta', 'greenhouse', 'zetaglobal'),
    ('Freshworks', 'smartrecruiters', 'Freshworks'),
    ('Swiggy', 'smartrecruiters', 'Swiggy'),
    ('Canva', 'smartrecruiters', 'Canva'),
    ('Wise', 'smartrecruiters', 'Wise'),
    ('ServiceNow', 'smartrecruiters', 'ServiceNow'),
    ('Experian', 'smartrecruiters', 'Experian'),
    ('Hugging Face', 'workable', 'huggingface'),
    ('Zyte', 'workable', 'zyte'),
]

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    companies = sa.table(
        "companies", sa.column("name", sa.Text), sa.column("ats", sa.Text), sa.column("slug", sa.Text),
        sa.column("origin", sa.Text),
    )
    op.execute(
        postgresql.insert(companies)
        .values([{"name": n, "ats": a, "slug": s, "origin": "seed"} for n, a, s in SEED])
        .on_conflict_do_nothing(index_elements=["ats", "slug"])
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM companies WHERE origin = 'seed'")

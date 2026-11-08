from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from pipeline.refresh import run_refresh
from sources.base import RawJob, SourceBlocked, SourceResult

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
SETTINGS = {
    "scoring": {"min_score": 30, "max_age_days": 21},
    "expiry": {"miss_limit": 2, "stale_days": 21},
    "rates_to_inr": {"USD": 88.0},
    "boards": {"source_timeout_s": 5},
}


class Fake:
    def __init__(
        self,
        name: str,
        result: SourceResult | None = None,
        error: Exception | None = None,
        config_key: str | None = None,
    ):
        self.name, self._result, self._error = name, result or SourceResult(), error
        if config_key:
            self.config_key = config_key

    async def fetch(self, client: Any, settings: dict[str, Any]) -> SourceResult:
        if self._error:
            raise self._error
        return self._result


def job(
    source="greenhouse",
    ext="1",
    title="DevOps Intern",
    company="GitLab",
    location="Remote",
    url="https://job-boards.greenhouse.io/gitlab/jobs/1",
    scope: str | None = "greenhouse:gitlab",
    **extra: Any,
):
    return RawJob(
        source=source,
        external_id=ext,
        title=title,
        company=company,
        apply_url=url,
        location=location,
        description="Python and Docker.",
        posted_at=NOW - timedelta(days=1),
        scope=scope,
        **extra,
    )


def rows(engine, sql):
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(text(sql)).all()]


def test_the_same_job_from_two_sources_is_stored_once_with_both_sources(db_engine):
    greenhouse = Fake("greenhouse", SourceResult(jobs=[job()], complete_scopes={"greenhouse:gitlab"}))
    linkedin = Fake(
        "jobspy:linkedin",
        SourceResult(
            jobs=[
                job(
                    source="jobspy:linkedin",
                    ext="li-9",
                    company="GitLab Inc.",
                    url="https://linkedin.com/jobs/9",
                    scope=None,
                )
            ]
        ),
    )

    summary = run_refresh(db_engine, [greenhouse, linkedin], SETTINGS, trigger="test", now=NOW)

    assert rows(db_engine, "SELECT title, company_name FROM jobs") == [("DevOps Intern", "GitLab")]
    assert sorted(rows(db_engine, "SELECT source FROM job_sources")) == [
        ("greenhouse",),
        ("jobspy:linkedin",),
    ]
    assert sorted(rows(db_engine, "SELECT source, status, fetched, new FROM run_sources")) == [
        ("greenhouse", "ok", 1, 1),
        ("jobspy:linkedin", "ok", 1, 0),
    ]
    assert rows(db_engine, "SELECT trigger, finished_at IS NOT NULL FROM refresh_runs") == [("test", True)]
    assert [j["title"] for j in summary.new_jobs] == ["DevOps Intern"]


def test_one_broken_or_blocked_source_never_fails_the_run(db_engine):
    sources = [
        Fake("remoteok", error=SourceBlocked("HTTP 429 from remoteok.com")),
        Fake("himalayas", error=RuntimeError("bad json")),
        Fake("greenhouse", SourceResult(jobs=[job()], warning="1 board failed: gone (HTTP 404)")),
    ]

    run_refresh(db_engine, sources, SETTINGS, trigger="test", now=NOW)

    assert sorted(rows(db_engine, "SELECT source, status, error_text FROM run_sources")) == [
        ("greenhouse", "ok", "1 board failed: gone (HTTP 404)"),
        ("himalayas", "error", "RuntimeError: bad json"),
        ("remoteok", "blocked", "HTTP 429 from remoteok.com"),
    ]
    assert rows(db_engine, "SELECT count(*) FROM jobs") == [(1,)]


def test_senior_off_role_wrong_city_and_stale_jobs_are_not_stored(db_engine):
    stale = job(ext="4", title="Backend Intern")
    stale.posted_at = NOW - timedelta(days=40)
    source = Fake(
        "greenhouse",
        SourceResult(
            jobs=[
                job(ext="1", title="Senior DevOps Engineer"),
                job(ext="2", title="Marketing Intern"),
                job(ext="3", title="SRE Intern", location="Mumbai, India"),
                stale,
                job(ext="5", title="Platform Engineering Intern"),
            ]
        ),
    )

    run_refresh(db_engine, [source], SETTINGS, trigger="test", now=NOW)

    assert rows(db_engine, "SELECT title FROM jobs") == [("Platform Engineering Intern",)]
    assert rows(db_engine, "SELECT fetched, new FROM run_sources") == [(5, 1)]


def test_salary_is_stored_in_lakhs_per_annum(db_engine):
    paid = job(salary_min=50_000, salary_max=60_000, salary_currency="USD", salary_period="yearly")
    run_refresh(db_engine, [Fake("greenhouse", SourceResult(jobs=[paid]))], SETTINGS, trigger="test", now=NOW)

    assert rows(db_engine, "SELECT salary_min_lpa, salary_max_lpa FROM jobs") == [(44.0, 52.8)]


def test_a_job_missing_from_a_complete_board_twice_is_ghosted_and_comes_back_if_reposted(db_engine):
    def board(*jobs, ok=True):
        if not ok:
            return Fake("greenhouse", error=SourceBlocked("HTTP 429"))
        return Fake("greenhouse", SourceResult(jobs=list(jobs), complete_scopes={"greenhouse:gitlab"}))

    run_refresh(db_engine, [board(job())], SETTINGS, trigger="test", now=NOW)
    run_refresh(db_engine, [board()], SETTINGS, trigger="test", now=NOW + timedelta(hours=6))
    assert rows(db_engine, "SELECT missed_runs, expired FROM jobs") == [(1, False)]

    run_refresh(db_engine, [board(ok=False)], SETTINGS, trigger="test", now=NOW + timedelta(hours=12))
    assert rows(db_engine, "SELECT missed_runs, expired FROM jobs") == [(1, False)]  # blocked ≠ missing

    run_refresh(db_engine, [board()], SETTINGS, trigger="test", now=NOW + timedelta(hours=18))
    assert rows(db_engine, "SELECT missed_runs, expired FROM jobs") == [(2, True)]

    run_refresh(db_engine, [board(job())], SETTINGS, trigger="test", now=NOW + timedelta(hours=24))
    assert rows(db_engine, "SELECT missed_runs, expired FROM jobs") == [(0, False)]


def test_feed_jobs_never_count_misses_but_go_stale_after_a_while(db_engine):
    feed = job(source="remotive", ext="r1", scope=None, url="https://remotive.com/x")
    run_refresh(db_engine, [Fake("remotive", SourceResult(jobs=[feed]))], SETTINGS, trigger="test", now=NOW)
    empty = Fake("remotive", SourceResult())

    run_refresh(db_engine, [empty], SETTINGS, trigger="test", now=NOW + timedelta(days=3))
    assert rows(db_engine, "SELECT missed_runs, expired FROM jobs") == [(0, False)]

    run_refresh(db_engine, [empty], SETTINGS, trigger="test", now=NOW + timedelta(days=22))
    assert rows(db_engine, "SELECT expired FROM jobs") == [(True,)]


def test_apply_links_on_ats_boards_add_the_company_and_link_the_job(db_engine):
    found = job(
        source="jsearch",
        ext="js-1",
        company="Razorpay",
        scope=None,
        url="https://jobs.lever.co/razorpay/abc-123",
    )

    run_refresh(db_engine, [Fake("jsearch", SourceResult(jobs=[found]))], SETTINGS, trigger="test", now=NOW)

    assert rows(db_engine, "SELECT name, ats, slug, origin FROM companies") == [
        ("Razorpay", "lever", "razorpay", "discovered")
    ]
    assert rows(db_engine, "SELECT company_id IS NOT NULL FROM jobs") == [(True,)]


def test_source_state_is_saved_for_the_next_run(db_engine):
    rotating = Fake("jsearch", SourceResult(state={"query_index": 4}), config_key="jsearch")
    settings = SETTINGS | {"jsearch": {"queries": [], "query_index": 3}}

    run_refresh(db_engine, [rotating], settings, trigger="test", now=NOW)

    assert rows(db_engine, "SELECT value->>'query_index' FROM settings WHERE key = 'jsearch'") == [("4",)]


def test_a_later_run_rescores_a_job_instead_of_keeping_the_old_high_score(db_engine):
    rich = job()
    rich.description = "Python Go Docker Kubernetes Terraform Linux."
    plain = job()
    plain.description = "Nothing special."

    run_refresh(db_engine, [Fake("greenhouse", SourceResult(jobs=[rich]))], SETTINGS, trigger="test", now=NOW)
    first = rows(db_engine, "SELECT score FROM jobs")[0][0]
    run_refresh(
        db_engine,
        [Fake("greenhouse", SourceResult(jobs=[plain]))],
        SETTINGS,
        trigger="test",
        now=NOW + timedelta(hours=6),
    )

    assert rows(db_engine, "SELECT score FROM jobs")[0][0] < first


def test_the_score_breakdown_is_stored_with_the_job(db_engine):
    run_refresh(
        db_engine, [Fake("greenhouse", SourceResult(jobs=[job()]))], SETTINGS, trigger="test", now=NOW
    )

    score, breakdown = rows(db_engine, "SELECT score, breakdown FROM jobs")[0]
    assert sum(points for _, points in breakdown) == score
    assert ["role: devops", 75] in breakdown

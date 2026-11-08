from datetime import timedelta

from pipeline.refresh import run_refresh
from sources.base import SourceBlocked, SourceResult
from tests.test_refresh import NOW, SETTINGS, Fake, job


def test_settings_can_be_read_and_edited(api, db_engine):
    saved = api.put("/settings/email_template", json={"subject": "Hi {company}", "body": "Hello {hr_name}"})
    assert saved.status_code == 200, saved.text

    everything = api.get("/settings").json()
    assert everything["email_template"] == {"subject": "Hi {company}", "body": "Hello {hr_name}"}


def test_settings_reject_unknown_keys_and_broken_templates(api):
    assert api.put("/settings/telegram_token", json={"x": 1}).status_code == 404
    assert api.put("/settings/email_template", json={"subject": "only a subject"}).status_code == 422
    assert api.put("/settings/notify", json=["not", "an", "object"]).status_code == 422


def test_settings_need_the_passphrase(api):
    api.headers.pop("X-Passphrase")
    assert api.get("/settings").status_code == 401


def test_logs_list_runs_newest_first_with_every_source(api, db_engine):
    run_refresh(
        db_engine, [Fake("greenhouse", SourceResult(jobs=[job()]))], SETTINGS, trigger="cron", now=NOW
    )
    run_refresh(
        db_engine,
        [Fake("greenhouse", SourceResult()), Fake("remoteok", error=SourceBlocked("HTTP 429"))],
        SETTINGS,
        trigger="manual",
        now=NOW + timedelta(hours=6),
    )

    runs = api.get("/logs/runs").json()["runs"]

    assert [r["trigger"] for r in runs] == ["manual", "cron"]
    assert runs[1]["total_new"] == 1
    newest = {s["source"]: s for s in runs[0]["sources"]}
    assert newest["remoteok"]["status"] == "blocked"
    assert newest["remoteok"]["error_text"] == "HTTP 429"
    assert newest["greenhouse"]["status"] == "ok"


def test_one_run_shows_the_jobs_it_found(api, db_engine):
    summary = run_refresh(
        db_engine, [Fake("greenhouse", SourceResult(jobs=[job()]))], SETTINGS, trigger="cron", now=NOW
    )

    run = api.get(f"/logs/runs/{summary.run_id}").json()

    assert [j["title"] for j in run["new_jobs"]] == ["DevOps Intern"]
    assert run["sources"][0]["fetched"] == 1
    assert api.get("/logs/runs/999999").status_code == 404

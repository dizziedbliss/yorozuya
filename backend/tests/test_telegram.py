import json

import httpx

from notify.telegram import build_message, send_new_jobs

JOBS = [
    {
        "id": 1,
        "title": "DevOps <Intern> & Co",
        "company": "Initvalue",
        "score": 240,
        "apply_url": "https://x.io/1",
    },
    {"id": 2, "title": "SRE Intern", "company": "Redis", "score": 165, "apply_url": "https://x.io/2"},
    {"id": 3, "title": "Backend Intern", "company": "Ramp", "score": 130, "apply_url": "https://x.io/3"},
    {"id": 4, "title": "Meh Engineer", "company": "Nobody", "score": 60, "apply_url": "https://x.io/4"},
]
NOTIFY = {"telegram_min_score": 120, "top_n": 2}


def test_message_lists_the_best_new_jobs_escaped_with_a_count_of_the_rest():
    text = build_message(JOBS, NOTIFY, site_url="https://yorozuya.dizziedbliss.lol")

    assert text is not None
    assert "3 new matches" in text  # the 60-pointer is below the bar
    assert '<a href="https://x.io/1">DevOps &lt;Intern&gt; &amp; Co</a>' in text
    assert "SRE Intern" in text and "Backend Intern" not in text
    assert "and 1 more" in text
    assert "https://yorozuya.dizziedbliss.lol" in text


def test_nothing_new_above_the_bar_means_no_message():
    assert build_message(JOBS[3:], NOTIFY, site_url="https://y") is None
    assert build_message([], NOTIFY, site_url="https://y") is None


def test_sending_posts_html_to_the_bot_api():
    sent: list[dict] = []

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/bottok123/sendMessage"
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = send_new_jobs(client, "tok123", "42", JOBS, NOTIFY, site_url="https://y")

    assert result == "sent"
    assert sent[0]["chat_id"] == "42" and sent[0]["parse_mode"] == "HTML"
    assert sent[0]["link_preview_options"] == {"is_disabled": True}


def test_a_telegram_failure_is_reported_not_swallowed():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(400, json={"ok": False, "description": "chat not found"})
        )
    ) as client:
        try:
            send_new_jobs(client, "tok", "42", JOBS, NOTIFY, site_url="https://y")
        except RuntimeError as exc:
            assert "chat not found" in str(exc)
        else:
            raise AssertionError("expected a RuntimeError")


def test_the_worker_logs_a_failed_ping_on_the_run(db_engine, monkeypatch):
    from sqlalchemy import text

    from pipeline.refresh import RunSummary
    from tests.test_refresh import NOW, SETTINGS, Fake, run_refresh
    from worker import refresh as worker

    summary = run_refresh(db_engine, [Fake("greenhouse")], SETTINGS, trigger="test", now=NOW)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    def refuse(*args, **kwargs):
        raise RuntimeError("Telegram said no (HTTP 400): chat not found")

    monkeypatch.setattr(worker, "send_new_jobs", refuse)
    result = worker.ping_telegram(db_engine, RunSummary(summary.run_id, {}, JOBS), {"notify": NOTIFY})

    assert result.startswith("failed")
    with db_engine.connect() as conn:
        row = conn.execute(text("SELECT status, error_text FROM run_sources WHERE source = 'telegram'")).one()
    assert row == ("error", "RuntimeError: Telegram said no (HTTP 400): chat not found")

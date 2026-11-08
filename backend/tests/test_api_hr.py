import httpx
import pytest

import hr.finder as finder
import main
from tests.conftest import add_job

HUNTER = "api.hunter.io/v2/domain-search"


def hunter_payload(emails: list, domain: str | None = "razorpay.com", pattern: str = "{first}.{last}"):
    return {
        "data": {"domain": domain, "pattern": pattern, "organization": "Razorpay", "emails": emails},
        "meta": {},
    }


def person(
    value: str,
    dept: str | None = "hr",
    position: str | None = "Talent Acquisition",
    confidence: int = 91,
    first: str = "Asha",
    last: str = "Rao",
):
    return {
        "value": value,
        "type": "personal",
        "confidence": confidence,
        "first_name": first,
        "last_name": last,
        "position": position,
        "department": dept,
    }


@pytest.fixture
def wire(api, monkeypatch):
    """Point the finder at fake Hunter answers and a fake MX check; returns the call log."""
    calls: list[dict] = []
    state = {"hunter": hunter_payload([]), "mx": {"razorpay.com"}}

    def handle(request: httpx.Request) -> httpx.Response:
        if f"{request.url.host}{request.url.path}" != HUNTER:
            return httpx.Response(404)
        calls.append(dict(request.url.params))
        answer = state["hunter"]
        return answer if isinstance(answer, httpx.Response) else httpx.Response(200, json=answer)

    monkeypatch.setenv("HUNTER_API_KEY", "hk")
    main.app.dependency_overrides[finder.http_client] = lambda: httpx.Client(
        transport=httpx.MockTransport(handle)
    )
    main.app.dependency_overrides[finder.mx_checker] = lambda: lambda domain: domain in state["mx"]
    yield calls, state
    main.app.dependency_overrides.clear()


def find(api, job_id):
    response = api.post(f"/fresher/jobs/{job_id}/find-hr")
    assert response.status_code == 200, response.text
    return response.json()


def test_an_email_in_the_posting_wins_without_spending_a_hunter_search(api, db_engine, wire):
    calls, _ = wire
    job_id = add_job(
        db_engine,
        company_name="Razorpay",
        description="Send your CV to campus.hiring@razorpay.com. Privacy: privacy@razorpay.com",
    )

    result = find(api, job_id)

    assert result["status"] == "found"
    assert [(c["email"], c["origin"]) for c in result["contacts"]] == [
        ("campus.hiring@razorpay.com", "posting")
    ]
    assert calls == []
    # cached on the company, so the job detail shows it too
    assert (
        api.get(f"/fresher/jobs/{job_id}").json()["hr_contacts"][0]["email"] == "campus.hiring@razorpay.com"
    )


def test_hunter_hr_people_are_kept_and_other_departments_dropped(api, db_engine, wire):
    calls, state = wire
    state["hunter"] = hunter_payload(
        [
            person("asha.rao@razorpay.com"),
            person("dev.k@razorpay.com", dept="it", position="Engineer"),
            person("careers@razorpay.com", dept=None, position=None, confidence=80) | {"type": "generic"},
        ]
    )
    job_id = add_job(db_engine, company_name="Razorpay")

    result = find(api, job_id)

    assert [(c["email"], c["origin"], c["confidence"]) for c in result["contacts"]] == [
        ("asha.rao@razorpay.com", "hunter", 91),
        ("careers@razorpay.com", "hunter", 80),
    ]
    assert result["contacts"][0]["name"] == "Asha Rao"
    assert calls[0]["company"] == "Razorpay" and calls[0]["api_key"] == "hk"
    assert calls[0]["department"] == "hr"  # spend the 10 free results on recruiters, not engineers
    assert result["domain"] == "razorpay.com"


def test_when_hunter_has_nobody_it_guesses_at_a_domain_that_takes_mail(api, db_engine, wire):
    job_id = add_job(db_engine, company_name="Razorpay")

    result = find(api, job_id)

    assert result["status"] == "found"
    assert {c["origin"] for c in result["contacts"]} == {"guess"}
    assert "careers@razorpay.com" in [c["email"] for c in result["contacts"]]


def test_a_miss_is_remembered_so_quota_is_not_spent_again(api, db_engine, wire):
    calls, state = wire
    state["hunter"] = hunter_payload([], domain=None)
    job_id = add_job(db_engine, company_name="Tiny Startup", apply_url="https://jobs.lever.co/tiny/1")

    first = find(api, job_id)
    second = find(api, job_id)

    assert first["status"] == "miss" and first["contacts"] == []
    assert second["status"] == "miss" and second["cached"] is True
    assert len(calls) == 1


def test_without_a_hunter_key_it_still_tries_the_free_steps(api, db_engine, wire, monkeypatch):
    calls, _ = wire
    monkeypatch.delenv("HUNTER_API_KEY")
    job_id = add_job(db_engine, company_name="Razorpay", apply_url="https://careers.razorpay.com/jobs/1")

    result = find(api, job_id)

    assert calls == []
    assert result["tried"] == ["posting", "guess"]
    assert "careers@razorpay.com" in [c["email"] for c in result["contacts"]]


def test_hunter_out_of_quota_falls_back_to_guessing(api, db_engine, wire):
    _, state = wire
    state["hunter"] = httpx.Response(429, json={"errors": [{"details": "quota"}]})
    job_id = add_job(db_engine, company_name="Razorpay", apply_url="https://careers.razorpay.com/jobs/1")

    result = find(api, job_id)

    assert result["status"] == "found"
    assert result["hunter_error"] == "Hunter refused (HTTP 429): out of searches this month?"
    assert {c["origin"] for c in result["contacts"]} == {"guess"}

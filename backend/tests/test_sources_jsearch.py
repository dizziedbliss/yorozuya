import httpx
import pytest

from sources.jsearch import JSearchSource
from tests.helpers import fake_client, fixture

pytestmark = pytest.mark.anyio

QUERIES = [
    {"query": "devops intern in Bengaluru", "country": "in"},
    {"query": "sre intern remote", "country": "us"},
    {"query": "backend fresher Chennai", "country": "in"},
]


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _settings(index=0, per_run=1):
    return {
        "jsearch": {
            "queries": QUERIES,
            "query_index": index,
            "requests_per_run": per_run,
            "min_remaining": 10,
        }
    }


def _client(calls, remaining="150"):
    def search(request: httpx.Request) -> httpx.Response:
        calls.append(dict(request.url.params) | {"key": request.headers.get("x-rapidapi-key")})
        return httpx.Response(
            200, json=fixture("jsearch"), headers={"x-ratelimit-requests-remaining": remaining}
        )

    return fake_client({"jsearch.p.rapidapi.com/search-v2": search})


async def test_spends_exactly_the_budget_and_rotates_to_the_next_query(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    calls: list[dict] = []

    result = await JSearchSource().fetch(_client(calls), _settings(index=2, per_run=2))

    assert [c["query"] for c in calls] == ["backend fresher Chennai", "devops intern in Bengaluru"]
    assert calls[0]["country"] == "in" and calls[0]["key"] == "k"
    assert result.state == {"query_index": 4}
    job = result.jobs[0]
    assert job.source == "jsearch"
    assert (job.title, job.company, job.location) == (
        "DevOps and Cloud Intern",
        "Initvalue",
        "Bengaluru, Karnataka",
    )
    assert job.apply_url.startswith("https://www.jobleads.com/")
    assert job.posted_at is not None and job.posted_at.day == 3


async def test_stops_before_eating_the_monthly_reserve(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    calls: list[dict] = []

    result = await JSearchSource().fetch(_client(calls, remaining="9"), _settings(per_run=3))

    assert len(calls) == 1  # learned the quota was low from the first answer, then stopped
    assert result.warning == "JSearch quota low (9 left this month); stopped early"


async def test_missing_key_is_an_error_not_a_silent_skip(monkeypatch):
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    with pytest.raises(RuntimeError, match="RAPIDAPI_KEY"):
        await JSearchSource().fetch(_client([]), _settings())

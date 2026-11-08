import pytest

from sources.boards import ArbeitnowSource, HimalayasSource, RemoteOkSource, RemotiveSource
from tests.helpers import fake_client, fixture

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_remotive_jobs_are_remote_with_parsed_salary():
    client = fake_client({"remotive.com/api/remote-jobs": fixture("remotive")})

    result = await RemotiveSource().fetch(client, {})

    job = result.jobs[0]
    assert job.source == "remotive"
    assert job.title == "US Remote Patient Care Advocate (Customer Service)"
    assert job.company == "VXI Global Solutions"
    assert job.location == "Remote (USA)"
    assert (job.salary_min, job.salary_max, job.salary_currency, job.salary_period) == (
        25_000,
        35_000,
        "USD",
        "yearly",
    )
    assert result.complete_scopes == set()  # a feed, not a full board: never marks jobs missed


async def test_remoteok_skips_the_legal_notice_and_reads_usd_salaries():
    client = fake_client({"remoteok.com/api": fixture("remoteok")})

    result = await RemoteOkSource().fetch(client, {})

    assert len(result.jobs) == 3  # first element is RemoteOK's legal notice
    job = result.jobs[0]
    assert (job.title, job.company, job.location) == ("Junior Market Analyst", "MEYA HOLDINGS", "Remote")
    assert (job.salary_min, job.salary_max, job.salary_currency) == (60_000, 80_000, "USD")
    assert job.posted_at is not None


async def test_himalayas_reads_location_restrictions_and_salary():
    client = fake_client({"himalayas.app/jobs/api": fixture("himalayas")})

    result = await HimalayasSource().fetch(client, {"himalayas_pages": 1})

    job = result.jobs[0]
    assert job.company == "Lemartec Corporation"
    assert job.location == "Remote (United States)"
    assert (job.salary_min, job.salary_max, job.salary_currency, job.salary_period) == (
        80_000,
        95_000,
        "USD",
        "yearly",
    )


async def test_arbeitnow_keeps_only_remote_jobs():
    client = fake_client({"www.arbeitnow.com/api/job-board-api": fixture("arbeitnow")})

    result = await ArbeitnowSource().fetch(client, {"arbeitnow_pages": 1})

    assert [job.title for job in result.jobs] == ["Founding Account Executive, New Business"]
    assert result.jobs[0].location == "Remote"


async def test_a_board_that_refuses_us_is_reported_as_blocked():
    from sources.base import SourceBlocked

    client = fake_client({"remoteok.com/api": 429})
    with pytest.raises(SourceBlocked):
        await RemoteOkSource().fetch(client, {})

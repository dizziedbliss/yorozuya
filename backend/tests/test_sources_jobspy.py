import logging

import pandas as pd
import pytest

from sources.base import SourceBlocked
from sources.jobspy_source import JobSpySource
from tests.helpers import fixture

pytestmark = pytest.mark.anyio

SETTINGS = {
    "jobspy": {
        "searches": [
            {"term": "devops intern", "location": "Bengaluru"},
            {"term": "software engineer fresher", "location": "Chennai"},
        ],
        "results_wanted": 50,
        "hours_old": 72,
        "index_indeed": 1,
    }
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_indeed_rows_become_jobs_and_the_search_rotates():
    calls = []

    def scrape(**kwargs):
        calls.append(kwargs)
        return pd.DataFrame(fixture("jobspy_indeed"))

    result = await JobSpySource("indeed", scrape=scrape).fetch(None, SETTINGS)

    assert calls[0]["site_name"] == ["indeed"]
    assert (calls[0]["search_term"], calls[0]["location"]) == ("software engineer fresher", "Chennai")
    assert calls[0]["country_indeed"] == "india" and calls[0]["results_wanted"] == 50
    assert result.state == {"index_indeed": 2}
    job = result.jobs[0]
    assert job.source == "jobspy:indeed"
    assert (job.title, job.company) == ("Technology Early Career Entry Program", "State Street")
    # Indeed says only "KA, India": tag it with the city we searched so the city filter keeps it.
    assert job.location == "Chennai (KA, India)"
    assert job.apply_url.startswith("https://statestreet.wd1.myworkdayjobs.com/")
    assert job.posted_at is not None and job.posted_at.day == 5


async def test_a_board_that_blocks_jobspy_is_reported_as_blocked():
    def scrape(**kwargs):
        logging.getLogger("jobspy.linkedin").error("429 Too Many Requests")
        return pd.DataFrame()

    with pytest.raises(SourceBlocked, match="429"):
        await JobSpySource("linkedin", scrape=scrape).fetch(None, SETTINGS)


async def test_other_scraper_errors_with_no_rows_are_errors():
    def scrape(**kwargs):
        logging.getLogger("jobspy.naukri").error("unexpected response shape")
        return pd.DataFrame()

    with pytest.raises(RuntimeError, match="unexpected response shape"):
        await JobSpySource("naukri", scrape=scrape).fetch(None, SETTINGS)

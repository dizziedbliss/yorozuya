import pytest

from sources.ats import AtsSource
from tests.helpers import fake_client, fixture

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_greenhouse_board_becomes_clean_jobs_and_a_complete_scope():
    client = fake_client({"boards-api.greenhouse.io/v1/boards/gitlab/jobs": fixture("greenhouse_gitlab")})
    settings = {"companies": [{"name": "GitLab", "ats": "greenhouse", "slug": "gitlab"}]}

    result = await AtsSource("greenhouse").fetch(client, settings)

    assert len(result.jobs) == 3
    job = result.jobs[0]
    assert job.source == "greenhouse"
    assert job.company == "GitLab"
    assert job.title == "AI Transformation Owner, CRO"
    assert job.location == "Remote, United States"
    assert job.apply_url == "https://job-boards.greenhouse.io/gitlab/jobs/8638232002"
    assert job.posted_at is not None and job.posted_at.year == 2026
    assert "&lt;" not in job.description and "<div" not in job.description
    assert job.description.startswith("GitLab is the intelligent")
    assert job.scope == "greenhouse:gitlab"
    assert result.complete_scopes == {"greenhouse:gitlab"}
    assert result.warning is None


async def test_a_dead_board_is_a_warning_not_a_failure():
    client = fake_client({"boards-api.greenhouse.io/v1/boards/gitlab/jobs": fixture("greenhouse_gitlab")})
    settings = {
        "companies": [
            {"name": "GitLab", "ats": "greenhouse", "slug": "gitlab"},
            {"name": "Gone Inc", "ats": "greenhouse", "slug": "gone"},
        ]
    }

    result = await AtsSource("greenhouse").fetch(client, settings)

    assert len(result.jobs) == 3
    assert result.complete_scopes == {"greenhouse:gitlab"}
    assert result.warning == "1 board failed: gone (HTTP 404)"


def _one(ats: str, slug: str, name: str):
    return {"companies": [{"name": name, "ats": ats, "slug": slug}]}


async def test_lever_board_uses_plain_text_and_millisecond_timestamps():
    client = fake_client({"api.lever.co/v0/postings/palantir": fixture("lever_palantir")})

    result = await AtsSource("lever").fetch(client, _one("lever", "palantir", "Palantir"))

    job = result.jobs[0]
    assert (job.title, job.company, job.location) == (
        "Administrative Business Partner",
        "Palantir",
        "Singapore, Singapore",
    )
    assert job.apply_url == "https://jobs.lever.co/palantir/6ed76ce8-4156-4b60-b120-403538bd66cd"
    assert job.posted_at is not None and job.posted_at.year == 2026
    assert job.description.startswith("A World-Changing Company")
    assert "What We Require" in job.description  # list sections are kept, headings included
    assert result.complete_scopes == {"lever:palantir"}


async def test_ashby_board_marks_remote_locations():
    client = fake_client({"api.ashbyhq.com/posting-api/job-board/supabase": fixture("ashby_supabase")})

    result = await AtsSource("ashby").fetch(client, _one("ashby", "supabase", "Supabase"))

    titles = {job.title: job for job in result.jobs}
    assert titles["AI Platform Engineer"].location == "Remote, Global"
    assert titles["AI Platform Engineer"].apply_url.startswith("https://jobs.ashbyhq.com/supabase/")
    posted = titles["Customer Solution Architect (AMER)"].posted_at
    assert posted is not None and posted.year == 2024


async def test_workable_board_marks_telecommuting_jobs_remote():
    client = fake_client(
        {"apply.workable.com/api/v1/widget/accounts/huggingface": fixture("workable_huggingface")}
    )

    result = await AtsSource("workable").fetch(client, _one("workable", "huggingface", "Hugging Face"))

    job = result.jobs[0]
    assert job.title == "Open-Source Machine Learning Engineer - EMEA Remote"
    assert job.location == "Remote (Paris, France)"
    assert job.apply_url == "https://apply.workable.com/j/81B46579FE"
    assert job.description  # html turned into text
    assert result.complete_scopes == {"workable:huggingface"}


async def test_smartrecruiters_only_opens_details_for_titles_in_my_roles():
    listing = fixture("smartrecruiters_freshworks")
    listing["totalFound"] = 3
    listing["content"][0]["name"] = "Backend Engineer Intern"
    detail_calls: list[str] = []

    def detail(request):
        detail_calls.append(request.url.path)
        import httpx

        return httpx.Response(200, json=fixture("smartrecruiters_freshworks_detail"))

    client = fake_client(
        {
            "api.smartrecruiters.com/v1/companies/Freshworks/postings": listing,
            "api.smartrecruiters.com/v1/companies/Freshworks/postings/744000160306729": detail,
        }
    )

    result = await AtsSource("smartrecruiters").fetch(
        client, _one("smartrecruiters", "Freshworks", "Freshworks")
    )

    assert [job.title for job in result.jobs] == ["Backend Engineer Intern"]
    assert detail_calls == ["/v1/companies/Freshworks/postings/744000160306729"]
    job = result.jobs[0]
    assert job.location == "San Mateo, CA, United States"
    assert job.apply_url.startswith("https://jobs.smartrecruiters.com/Freshworks/744000160306729")
    assert "Qualifications" in job.description
    assert result.complete_scopes == {"smartrecruiters:Freshworks"}

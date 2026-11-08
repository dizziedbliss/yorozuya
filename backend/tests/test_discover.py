import pytest

from pipeline.discover import ats_from_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://boards.greenhouse.io/razorpaysoftwareprivatelimited/jobs/123",
            ("greenhouse", "razorpaysoftwareprivatelimited"),
        ),
        ("https://job-boards.greenhouse.io/gitlab/jobs/8638232002?gh_src=x", ("greenhouse", "gitlab")),
        ("https://job-boards.eu.greenhouse.io/deliveryhero/jobs/1", ("greenhouse", "deliveryhero")),
        ("https://jobs.lever.co/palantir/6ed76ce8-4156", ("lever", "palantir")),
        ("https://jobs.eu.lever.co/mews/abc", ("lever", "mews")),
        ("https://jobs.ashbyhq.com/supabase/3b5d54ca", ("ashby", "supabase")),
        ("https://apply.workable.com/huggingface/j/81B46579FE/", ("workable", "huggingface")),
        ("https://jobs.smartrecruiters.com/Freshworks/744000160306729-x", ("smartrecruiters", "Freshworks")),
        # Things that look close but aren't a company board:
        ("https://apply.workable.com/j/81B46579FE", None),
        ("https://boards.greenhouse.io/embed/job_app?for=x", None),
        ("https://in.indeed.com/viewjob?jk=1", None),
        ("", None),
    ],
)
def test_apply_urls_on_public_ats_boards_reveal_the_company(url, expected):
    assert ats_from_url(url) == expected

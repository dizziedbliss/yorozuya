from tests.conftest import add_job


def titles(response):
    assert response.status_code == 200, response.text
    return [job["title"] for job in response.json()["jobs"]]


def test_the_list_needs_the_passphrase(api):
    api.headers.pop("X-Passphrase")
    assert api.get("/fresher/jobs").status_code == 401


def test_jobs_come_best_first_with_sources_status_and_chips(api, db_engine):
    add_job(db_engine, title="Backend Intern", score=90, sources=["lever", "jsearch"])
    add_job(db_engine, title="DevOps Intern", score=200)

    response = api.get("/fresher/jobs")

    assert titles(response) == ["DevOps Intern", "Backend Intern"]
    body = response.json()
    assert body["total"] == 2
    second = body["jobs"][1]
    assert sorted(second["sources"]) == ["jsearch", "lever"]
    assert second["status"] == "new"
    assert second["matched"] == ["devops", "intern"] and second["techs"] == ["docker"]
    assert "description" not in second  # the list stays light; detail has it


def test_ghosted_jobs_hide_unless_asked_but_applied_ones_never_hide(api, db_engine):
    add_job(db_engine, title="Live Intern")
    gone = add_job(db_engine, title="Ghosted Intern", expired=True)
    applied = add_job(db_engine, title="Applied Ghosted Intern", expired=True)
    api.patch(f"/fresher/jobs/{applied}/status", json={"status": "applied"})

    assert sorted(titles(api.get("/fresher/jobs"))) == ["Applied Ghosted Intern", "Live Intern"]
    assert len(titles(api.get("/fresher/jobs", params={"include_expired": True}))) == 3
    assert gone


def test_filters_by_place_role_source_status_and_text(api, db_engine):
    add_job(
        db_engine,
        title="SRE Intern",
        location="Chennai, India",
        matched=["sre", "intern"],
        sources=["naukri"],
    )
    add_job(db_engine, title="Backend Intern", location="Remote (USA)", matched=["backend", "intern"])
    blr = add_job(db_engine, title="DevOps Intern", location="Bangalore", company_name="Razorpay")
    api.patch(f"/fresher/jobs/{blr}/status", json={"status": "skipped"})

    assert titles(api.get("/fresher/jobs", params={"where": "chennai"})) == ["SRE Intern"]
    assert titles(api.get("/fresher/jobs", params={"where": "bengaluru"})) == ["DevOps Intern"]
    assert titles(api.get("/fresher/jobs", params={"where": "remote"})) == ["Backend Intern"]
    assert titles(api.get("/fresher/jobs", params={"role": "sre"})) == ["SRE Intern"]
    assert titles(api.get("/fresher/jobs", params={"source": "naukri"})) == ["SRE Intern"]
    assert titles(api.get("/fresher/jobs", params={"status": "skipped"})) == ["DevOps Intern"]
    assert titles(api.get("/fresher/jobs", params={"q": "razorpay"})) == ["DevOps Intern"]


def test_salary_range_filter_keeps_unpaid_listings_unless_told_not_to(api, db_engine):
    add_job(db_engine, title="Rich Intern", salary_min_lpa=12.0, salary_max_lpa=18.0)
    add_job(db_engine, title="Poor Intern", salary_min_lpa=2.0, salary_max_lpa=3.0)
    add_job(db_engine, title="Vibes Intern")

    in_range = titles(api.get("/fresher/jobs", params={"salary_min": 10, "salary_max": 20}))
    assert sorted(in_range) == ["Rich Intern", "Vibes Intern"]
    strict = titles(api.get("/fresher/jobs", params={"salary_min": 10, "include_no_salary": False}))
    assert strict == ["Rich Intern"]


def test_detail_has_the_description_and_source_links(api, db_engine):
    job_id = add_job(db_engine, title="DevOps Intern", description="Requirements:\nDocker.")

    detail = api.get(f"/fresher/jobs/{job_id}")

    assert detail.status_code == 200
    assert detail.json()["description"] == "Requirements:\nDocker."
    assert detail.json()["hr_contacts"] == []
    assert api.get("/fresher/jobs/999999").status_code == 404


def test_status_changes_are_saved_and_validated(api, db_engine):
    job_id = add_job(db_engine)

    ok = api.patch(f"/fresher/jobs/{job_id}/status", json={"status": "emailed", "note": "sent to hr@"})
    assert ok.status_code == 200 and ok.json()["status"] == "emailed"
    assert api.get(f"/fresher/jobs/{job_id}").json()["status"] == "emailed"

    assert api.patch(f"/fresher/jobs/{job_id}/status", json={"status": "vibing"}).status_code == 422
    assert api.patch("/fresher/jobs/999999/status", json={"status": "applied"}).status_code == 404

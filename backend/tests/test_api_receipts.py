from tests.conftest import add_job


def test_detail_returns_the_score_breakdown(api, db_engine):
    job_id = add_job(db_engine, score=105, breakdown=[["role: devops", 75], ["location: bengaluru", 30]])

    detail = api.get(f"/fresher/jobs/{job_id}").json()

    assert detail["breakdown"] == [
        {"label": "role: devops", "points": 75},
        {"label": "location: bengaluru", "points": 30},
    ]


def test_every_status_change_is_kept_as_history(api, db_engine):
    job_id = add_job(db_engine)

    for status, note in [("applied", None), ("emailed", "emailed hr@"), ("heard_back", "recruiter replied")]:
        assert (
            api.patch(f"/fresher/jobs/{job_id}/status", json={"status": status, "note": note}).status_code
            == 200
        )

    receipt = api.get("/fresher/receipts").json()["jobs"][0]
    assert receipt["status"] == "heard_back"
    assert [(e["status"], e["note"]) for e in receipt["events"]] == [
        ("applied", None),
        ("emailed", "emailed hr@"),
        ("heard_back", "recruiter replied"),
    ]


def test_the_new_stages_are_accepted_and_typos_are_not(api, db_engine):
    job_id = add_job(db_engine)
    for status in ["interview", "offer", "rejected", "ghosted"]:
        assert api.patch(f"/fresher/jobs/{job_id}/status", json={"status": status}).status_code == 200
    assert api.patch(f"/fresher/jobs/{job_id}/status", json={"status": "heard back"}).status_code == 422


def test_receipts_list_only_what_was_sent_with_stats_and_activity(api, db_engine):
    ids = {
        name: add_job(db_engine, title=name)
        for name in ["A Intern", "B Intern", "C Intern", "D Intern", "E Intern"]
    }
    moves = {
        "A Intern": ["applied", "emailed", "heard_back", "interview"],
        "B Intern": ["applied", "ghosted"],
        "C Intern": ["applied", "rejected"],
        "D Intern": ["skipped"],
    }
    for name, steps in moves.items():
        for step in steps:
            api.patch(f"/fresher/jobs/{ids[name]}/status", json={"status": step})

    body = api.get("/fresher/receipts").json()

    assert sorted(j["title"] for j in body["jobs"]) == ["A Intern", "B Intern", "C Intern"]
    assert body["stats"] == {
        "sent": 3,
        "emailed": 1,
        "replies": 1,
        "interviews": 1,
        "offers": 0,
        "rejected": 1,
        "ghosted": 1,
    }
    assert len(body["activity"]) == 14
    assert body["activity"][-1]["applied"] == 3  # all applied today
    assert "description" not in body["jobs"][0]


def test_receipts_need_the_passphrase(api):
    api.headers.pop("X-Passphrase")
    assert api.get("/fresher/receipts").status_code == 401

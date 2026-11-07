import pytest
from fastapi.testclient import TestClient

import main
from routers import curated

PASS = "correct horse battery staple"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SITE_PASSPHRASE", PASS)
    # No companies = no live Greenhouse calls; the routes still run end to end.
    monkeypatch.setattr(curated, "companies", [])
    return TestClient(main.app)


def test_curated_jobs_needs_the_passphrase(client):
    assert client.get("/curated/jobs").status_code == 401
    assert client.get("/curated/jobs", headers={"X-Passphrase": "nope"}).status_code == 401

    ok = client.get("/curated/jobs", headers={"X-Passphrase": PASS})
    assert ok.status_code == 200
    assert ok.json() == []


def test_locked_routes_refuse_everyone_when_no_passphrase_is_configured(client, monkeypatch):
    monkeypatch.delenv("SITE_PASSPHRASE")
    response = client.get("/curated/jobs", headers={"X-Passphrase": ""})
    assert response.status_code == 503


def test_legacy_jobs_route_stays_open_until_the_new_frontend_ships(client):
    assert client.get("/jobs").status_code == 200


def test_health_reports_the_database_up(client, monkeypatch, database_url):
    monkeypatch.setenv("DATABASE_URL", database_url)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "up"}


def test_health_reports_the_database_down_honestly(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody:nothing@127.0.0.1:1/none")
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": "down"}

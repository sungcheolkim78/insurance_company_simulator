import pytest
from fastapi.testclient import TestClient

import app.db as db
from app.main import app, parse_allowed_origins

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_works_without_session_cookie():
    fresh_client = TestClient(app)
    fresh_client.cookies.clear()
    response = fresh_client.get("/health")
    assert response.status_code == 200


def test_cors_allows_credentialed_requests():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-credentials"] == "true"


def test_parse_allowed_origins_splits_and_trims():
    assert parse_allowed_origins("https://a.example , https://b.example") == [
        "https://a.example",
        "https://b.example",
    ]


def test_parse_allowed_origins_rejects_wildcard():
    # Credentials (cookies) are always enabled, so a wildcard origin would
    # expose the session cookie to any site.
    with pytest.raises(ValueError):
        parse_allowed_origins("*")
    with pytest.raises(ValueError):
        parse_allowed_origins("https://a.example, *")


def test_database_url_defaults_to_sqlite():
    assert str(db.database_url()).startswith("sqlite")

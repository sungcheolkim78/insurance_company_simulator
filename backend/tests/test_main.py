from fastapi.testclient import TestClient

import app.db as db
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_credentialed_requests():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-credentials"] == "true"


def test_database_url_defaults_to_sqlite():
    assert str(db.database_url()).startswith("sqlite")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.db as db
from app import models as _models
from app.db import get_session
from app.main import app

CSRF_COOKIE_NAME = "insurance_csrf"


def csrf_headers(client) -> dict[str, str]:
    """Obtain the CSRF cookie (issued on any GET) and return the matching header."""
    if CSRF_COOKIE_NAME not in client.cookies:
        client.get("/health")
    return {"X-CSRF-Token": client.cookies[CSRF_COOKIE_NAME]}


def register_user(client, email: str, password: str = "long-enough-pass") -> dict:
    """Register an account on the given client and return the user payload."""
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


class CsrfTestClient(TestClient):
    """TestClient that automatically attaches the CSRF header to unsafe requests,
    mirroring what the production Axios client does."""

    def request(self, method, url, **kwargs):
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            headers = dict(kwargs.pop("headers", None) or {})
            headers.update(csrf_headers(self))
            kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(db, "engine", engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with CsrfTestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def two_users(client):
    """Two authenticated clients (alice, bob) sharing one test database."""
    register_user(client, "alice@example.com")
    bob = CsrfTestClient(app)
    register_user(bob, "bob@example.com")
    return client, bob

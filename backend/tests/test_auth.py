from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie

import pytest
from fastapi import Depends, FastAPI, Response
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.auth import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)
from app.db import get_session
from app.models import SessionRow, UserRow


@pytest.fixture(autouse=True)
def _deterministic_cookie_env(monkeypatch):
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_SAMESITE", raising=False)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def user(engine):
    with Session(engine) as session:
        row = UserRow(email="ceo@example.com", password_hash=hash_password("correct-horse-battery"))
        session.add(row)
        session.commit()
        session.refresh(row)
        return row


def _new_session_row(engine, user: UserRow, token: str, *, expires_at: datetime | None = None) -> None:
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add(
            SessionRow(
                user_id=user.id,
                token_hash=hash_token(token),
                expires_at=expires_at or now + timedelta(days=1),
                created_at=now,
                last_used_at=now,
            )
        )
        session.commit()


@pytest.fixture()
def auth_client(engine, user):
    test_app = FastAPI()

    @test_app.get("/whoami")
    def whoami(current_user: UserRow = Depends(get_current_user)) -> dict:
        return {"id": current_user.id, "email": current_user.email}

    def override_get_session():
        with Session(engine) as session:
            yield session

    test_app.dependency_overrides[get_session] = override_get_session
    with TestClient(test_app) as client:
        yield client, engine, user


# --- password hashing -------------------------------------------------------


def test_hash_password_differs_from_plaintext():
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert hashed.startswith("$argon2")


def test_verify_password_accepts_valid_and_rejects_invalid():
    hashed = hash_password("s3cret-password")
    assert verify_password("s3cret-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_malformed_hash():
    assert verify_password("s3cret-password", "not-a-hash") is False


# --- session primitives -----------------------------------------------------


def test_create_session_sets_cookie_and_stores_only_hash(engine, user):
    with Session(engine) as session:
        response = Response()
        create_session(session, user, response)
        rows = session.exec(select(SessionRow)).all()

    assert len(rows) == 1
    jar = SimpleCookie()
    jar.load(response.headers["set-cookie"])
    morsel = jar[SESSION_COOKIE_NAME]
    assert morsel.value, "session cookie must carry the raw token"
    assert morsel["httponly"] is True
    assert morsel["path"] == "/"
    assert morsel["max-age"] == str(SESSION_MAX_AGE_SECONDS)
    assert rows[0].token_hash == hash_token(morsel.value)
    assert morsel.value not in rows[0].token_hash


def test_get_current_user_returns_user_for_valid_session(auth_client):
    client, engine, user = auth_client
    _new_session_row(engine, user, "raw-session-token")
    client.cookies.set(SESSION_COOKIE_NAME, "raw-session-token")

    response = client.get("/whoami")

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "email": user.email}


def test_get_current_user_updates_last_used_at(auth_client):
    client, engine, user = auth_client
    _new_session_row(engine, user, "raw-session-token")
    client.cookies.set(SESSION_COOKIE_NAME, "raw-session-token")

    before = datetime.now(timezone.utc) - timedelta(seconds=5)
    response = client.get("/whoami")
    assert response.status_code == 200

    with Session(engine) as session:
        row = session.exec(select(SessionRow)).first()
    assert row.last_used_at.replace(tzinfo=timezone.utc) > before


def test_get_current_user_rejects_missing_cookie(auth_client):
    client, _, _ = auth_client
    response = client.get("/whoami")
    assert response.status_code == 401


def test_get_current_user_rejects_unknown_token(auth_client):
    client, _, _ = auth_client
    client.cookies.set(SESSION_COOKIE_NAME, "no-such-token")
    response = client.get("/whoami")
    assert response.status_code == 401


def test_get_current_user_rejects_expired_session(auth_client):
    client, engine, user = auth_client
    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    _new_session_row(engine, user, "expired-token", expires_at=expired)
    client.cookies.set(SESSION_COOKIE_NAME, "expired-token")

    response = client.get("/whoami")

    assert response.status_code == 401


def test_get_current_user_rejects_inactive_user(auth_client):
    client, engine, user = auth_client
    with Session(engine) as session:
        stored = session.get(UserRow, user.id)
        stored.is_active = False
        session.add(stored)
        session.commit()
    _new_session_row(engine, user, "raw-session-token")
    client.cookies.set(SESSION_COOKIE_NAME, "raw-session-token")

    response = client.get("/whoami")

    assert response.status_code == 401


# --- CSRF / origin protection (wired into the real app) ---------------------


def test_unsafe_request_without_csrf_token_is_rejected(client):
    client.get("/health")
    response = client.post("/health")
    assert response.status_code == 403


def test_unsafe_request_without_csrf_cookie_is_rejected(client):
    response = client.post("/health", headers={"X-CSRF-Token": "anything"})
    assert response.status_code == 403


def test_unsafe_request_with_matching_csrf_token_passes_protection(client):
    client.get("/health")
    token = client.cookies[CSRF_COOKIE_NAME]
    response = client.post("/health", headers={"X-CSRF-Token": token})
    assert response.status_code == 405


def test_unsafe_request_with_mismatched_csrf_token_is_rejected(client):
    client.get("/health")
    response = client.post("/health", headers={"X-CSRF-Token": "mismatched-value"})
    assert response.status_code == 403


def test_unsafe_request_from_disallowed_origin_is_rejected(client):
    client.get("/health")
    token = client.cookies[CSRF_COOKIE_NAME]
    response = client.post(
        "/health",
        headers={"X-CSRF-Token": token, "Origin": "https://evil.example"},
    )
    assert response.status_code == 403


def test_safe_requests_do_not_require_csrf_token(client):
    response = client.get("/health")
    assert response.status_code == 200

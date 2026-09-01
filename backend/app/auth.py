import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, Response
from sqlmodel import Session, select

from .db import get_session
from .models import SessionRow, UserRow

SESSION_COOKIE_NAME = "insurance_session"
CSRF_COOKIE_NAME = "insurance_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_password_hasher = PasswordHasher()


def _cookie_secure() -> bool:
    return os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"


def _cookie_samesite() -> str:
    return os.environ.get("SESSION_COOKIE_SAMESITE", "lax")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(session: Session, user: UserRow, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session.add(
        SessionRow(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=now + timedelta(seconds=SESSION_MAX_AGE_SECONDS),
            created_at=now,
            last_used_at=now,
        )
    )
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        path="/",
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
    )


def issue_csrf_cookie(request: Request, response: Response) -> None:
    if CSRF_COOKIE_NAME in request.cookies:
        return
    response.set_cookie(
        CSRF_COOKIE_NAME,
        secrets.token_urlsafe(32),
        httponly=False,
        path="/",
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
    )


def require_csrf(request: Request) -> None:
    if request.method not in UNSAFE_METHODS:
        return
    # Browsers always attach a truthful Origin header to unsafe requests and JS
    # cannot forge it, so a known origin is sufficient protection. The
    # double-submit token below stays as the defense for cookie-bearing
    # requests that lack Origin (API clients); it cannot be enforced for the
    # deployed cross-site frontend because document.cookie cannot read the
    # API host's cookies there.
    origin = request.headers.get("origin")
    if origin:
        from .main import allowed_origins

        if origin not in allowed_origins:
            raise HTTPException(status_code=403, detail="Origin not allowed")
        return
    header = request.headers.get(CSRF_HEADER_NAME)
    cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie or not header or not secrets.compare_digest(header.encode(), cookie.encode()):
        raise HTTPException(status_code=403, detail="CSRF check failed")


def get_current_user(request: Request, session: Session = Depends(get_session)) -> UserRow:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    row = session.exec(select(SessionRow).where(SessionRow.token_hash == hash_token(token))).first()
    if row is None or _as_utc(row.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = session.get(UserRow, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Not authenticated")
    row.last_used_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    return user

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import Session, select

from ..auth import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    create_session,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)
from ..db import get_session
from ..models import LoginAttemptRow, SessionRow, UserRow
from ..schemas import LoginRequest, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

RATE_LIMIT_WINDOW = timedelta(minutes=15)
RATE_LIMIT_MAX_FAILURES = 5
GENERIC_LOGIN_ERROR = "Incorrect email or password"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _clear_login_attempts(session: Session, email: str, ip: str) -> None:
    for row in session.exec(
        select(LoginAttemptRow)
        .where(LoginAttemptRow.normalized_email == email)
        .where(LoginAttemptRow.client_ip == ip)
    ).all():
        session.delete(row)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    payload: RegisterRequest, response: Response, session: Session = Depends(get_session)
) -> UserResponse:
    existing = session.exec(select(UserRow).where(UserRow.email == payload.email)).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Unable to register with this email")

    user = UserRow(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    session.flush()
    create_session(session, user, response)
    session.commit()
    session.refresh(user)
    return UserResponse(id=user.id, email=user.email)


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest, request: Request, response: Response, session: Session = Depends(get_session)
) -> UserResponse:
    ip = _client_ip(request)
    cutoff = (datetime.now(timezone.utc) - RATE_LIMIT_WINDOW).replace(tzinfo=None)
    recent_failures = len(
        session.exec(
            select(LoginAttemptRow)
            .where(LoginAttemptRow.normalized_email == payload.email)
            .where(LoginAttemptRow.client_ip == ip)
            .where(LoginAttemptRow.attempted_at >= cutoff)
        ).all()
    )
    if recent_failures >= RATE_LIMIT_MAX_FAILURES:
        raise HTTPException(status_code=429, detail="Too many login attempts")

    user = session.exec(select(UserRow).where(UserRow.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash) or not user.is_active:
        session.add(LoginAttemptRow(normalized_email=payload.email, client_ip=ip))
        session.commit()
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)

    _clear_login_attempts(session, payload.email, ip)
    create_session(session, user, response)
    session.commit()
    session.refresh(user)
    return UserResponse(id=user.id, email=user.email)


@router.post("/logout")
def logout(request: Request, response: Response, session: Session = Depends(get_session)) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        row = session.exec(select(SessionRow).where(SessionRow.token_hash == hash_token(token))).first()
        if row is not None:
            session.delete(row)
            session.commit()
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", samesite="lax")
    return {"logged_out": True}


@router.get("/me", response_model=UserResponse)
def me(current_user: UserRow = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email)

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.auth import router as auth_router
from .api.games import router as games_router
from .auth import UNSAFE_METHODS, issue_csrf_cookie, require_csrf
from .db import init_db

app = FastAPI(title="Insurance Company Simulator")

_default_origins = "http://localhost:5173"


def parse_allowed_origins(raw: str) -> list[str]:
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("CORS wildcard origin is forbidden because requests carry credentials")
    return origins


allowed_origins = parse_allowed_origins(os.environ.get("CORS_ALLOWED_ORIGINS", _default_origins))


@app.middleware("http")
async def csrf_protection(request, call_next):
    if request.method in UNSAFE_METHODS:
        try:
            require_csrf(request)
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    response = await call_next(request)
    if request.method == "GET":
        issue_csrf_cookie(request, response)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(games_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

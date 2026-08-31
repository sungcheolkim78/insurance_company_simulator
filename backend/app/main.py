import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.games import router as games_router
from .db import init_db

app = FastAPI(title="Insurance Company Simulator")

_default_origins = "http://localhost:5173"
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

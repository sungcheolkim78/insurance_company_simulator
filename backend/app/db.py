import os
from pathlib import Path
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "simulator.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DEFAULT_DATABASE_URL = f"sqlite:///{DB_PATH}"



def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


def _configured_database_url() -> str:
    return _normalize_database_url(os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL)


def database_url() -> str:
    return _configured_database_url()


def create_app_engine(database_url: str | None = None) -> Engine:
    url = _normalize_database_url(database_url) if database_url is not None else _configured_database_url()
    engine_options = {}
    if url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **engine_options)


engine = create_app_engine()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session

from pathlib import Path
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "simulator.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DEFAULT_DATABASE_URL = f"sqlite:///{DB_PATH}"


def database_url() -> str:
    return DEFAULT_DATABASE_URL


def create_app_engine(database_url: str | None = None) -> Engine:
    url = database_url or DEFAULT_DATABASE_URL
    return create_engine(url, connect_args={"check_same_thread": False})


engine = create_app_engine()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session

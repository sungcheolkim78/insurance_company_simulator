import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from pathlib import Path
import tempfile

from app.db import get_session
from app.main import app
from app import models  # noqa: F401 - imported to register models with SQLModel


@pytest.fixture()
def client():
    # Use a temporary file-based database for tests
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(engine)

        def override_get_session():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("SYNC_API_KEY", "test-api-key")
os.environ.setdefault("TM_HTTP_TIMEOUT_S", "5")
os.environ.setdefault("TM_MAX_RETRIES", "1")
os.environ.setdefault("TM_BACKOFF_BASE_S", "0")
os.environ.setdefault("TM_RATE_LIMIT_RPS", "50")
os.environ.setdefault("SYNC_MAX_BATCH", "3")
os.environ.setdefault("SYNC_MAX_CLUB_PLAYERS", "3")

from app.db.base import Base
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    db_path = tmp_path / "repository_test.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)

    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )

    with testing_session_local() as session:
        yield session

    engine.dispose()

"""
Fixtures for tests that need a real PostgreSQL instance (duplicate-bucket
enforcement relies on Postgres' `ON CONFLICT`, and JSON columns behave
slightly differently across backends, so we test against the real engine
rather than sqlite).

These tests run automatically inside `docker compose -f docker-compose.test.yml`
(see README), and are skipped locally if no reachable Postgres is configured
via DATABASE URL env vars - so `pytest` still succeeds out of the box for the
pure-logic tests (sensor parsing, bucketing).
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base
from app import models  # noqa: F401


@pytest.fixture(scope="session")
def db_engine():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("No reachable PostgreSQL database configured for integration tests")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    # Clean slate between tests.
    session.execute(text("TRUNCATE measurements, sensors RESTART IDENTITY CASCADE"))
    session.commit()
    yield session
    session.close()

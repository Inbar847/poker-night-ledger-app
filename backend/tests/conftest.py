"""
Shared test fixtures.

Uses an in-memory SQLite database so PostgreSQL is not required to run the
test suite. StaticPool ensures all SQLAlchemy sessions share the same
underlying connection, which is required for in-memory SQLite.
"""

import os

# Set required env vars before any app module is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers all models with Base.metadata
from app.database.session import Base, get_db
from app.main import app

_TEST_DATABASE_URL = "sqlite:///:memory:"

_engine = create_engine(
    _TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign key enforcement for SQLite (off by default)
@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture(autouse=True)
def _clear_tables():
    """Delete all rows between tests to ensure isolation."""
    yield
    with _TestingSessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()


@pytest.fixture
def client():
    def _override_get_db():
        db = _TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Yield a SQLAlchemy session connected to the test database.

    Use this fixture in tests that need to query DB state directly
    (e.g. to verify notification side-effects).
    """
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

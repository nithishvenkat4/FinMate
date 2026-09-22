"""Pytest test configuration and shared fixtures."""

import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User

# In-memory SQLite database for isolated fast testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initializes the in-memory database schema once per session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yields a database session that rolls back changes after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Ensure a default test user exists
    user = session.query(User).filter(User.email == "demo@finmate.local").first()
    if not user:
        user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Test User",
            email="demo@finmate.local"
        )
        session.add(user)
        session.commit()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session, monkeypatch) -> Generator[TestClient, None, None]:
    """Provides a FastAPI test client wired to the transactional test DB session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    import app.api.v1.endpoints.health as health_module
    monkeypatch.setattr(health_module, "check_db_health", lambda: True)

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


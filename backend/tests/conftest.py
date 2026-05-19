import os

os.environ.setdefault("JWT_SECRET", "pytest-ci-secret-key-do-not-use-in-prod-32ch!")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.usuario import Usuario

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    user = Usuario(
        email="admin@dudo.com",
        nombre="Admin",
        password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(autouse=True, scope="session")
def disable_rate_limit():
    """Disable the slowapi rate limiter for all tests by default.

    This prevents rate-limit state bleed between tests and avoids flakiness
    from tests that call /auth/login repeatedly. Tests that explicitly want to
    exercise 429 behavior must use the enable_rate_limit fixture instead.
    """
    from app.security.rate_limit import limiter

    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def enable_rate_limit():
    """Opt-in fixture for tests that need the rate limiter active.

    Enables the limiter and resets its in-memory storage at both entry and exit
    so that test runs don't bleed into each other. The limiter is disabled again
    after the test completes.
    """
    from app.security.rate_limit import limiter

    limiter.reset()
    limiter.enabled = True

    yield

    limiter.enabled = False
    limiter.reset()  # clean up so the next test starts fresh

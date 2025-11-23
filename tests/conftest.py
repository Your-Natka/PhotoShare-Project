import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.database.models import Base
from app.database.connect_db import get_db
import app.cache   

sys.path.append(os.getcwd())

# -----------------------------
# Test database (SQLite)
# -----------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------
# DB fixture for each function
# -----------------------------
@pytest.fixture(scope="function")
def db_session():
    # створюємо чисту базу для кожного тесту
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

# -----------------------------
# Mock Redis for all tests
# -----------------------------
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    fake_redis = MagicMock()
    fake_redis.ping = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.set = AsyncMock()

    monkeypatch.setattr(app.cache, "redis_cache", fake_redis)

# -----------------------------
# FastAPI TestClient fixture
# -----------------------------
@pytest.fixture(scope="function")
def client(db_session):
    # override get_db to use test session
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

# -----------------------------
# Create test user fixture
# -----------------------------
@pytest.fixture(scope="function")
def create_user(db_session):
    from app.database.models import User
    from app.services.auth import get_password_hash

    user = User(
        username="artur4ik",
        email="artur4ik@example.com",
        password=get_password_hash("123456789"),
        role="Administrator",
        avatar="url-avatar"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

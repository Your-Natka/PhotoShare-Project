import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connect_db import Base, get_db
from app.database.models import User, Post
from app.main import app
import uuid

# -----------------------------
# Тестова база даних (in-memory SQLite)
# -----------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Створює таблиці перед усією сесією тестів і видаляє після"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Сесія для тесту з rollback після кожного тесту"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# -----------------------------
# Моки зовнішніх сервісів
# -----------------------------
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Мок Redis для всіх тестів"""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.ping.return_value = True
    monkeypatch.setattr("app.main.redis.from_url", lambda *a, **k: mock)
    return mock

@pytest.fixture()
def mock_cloudinary(monkeypatch):
    """Мок Cloudinary uploader"""
    mock = MagicMock()
    mock.upload.return_value = {"url": "https://fakeurl.com/fake.png", "public_id": "test_id"}
    mock.destroy.return_value = {"result": "ok"}
    monkeypatch.setattr("app.utils.cloudinary.uploader", mock)
    return mock

# -----------------------------
# FastAPI TestClient
# -----------------------------
@pytest.fixture(scope="function")
def client(db_session):
    # підміняємо залежність get_db на тестову сесію
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

# -----------------------------
# Тестові дані
# -----------------------------
@pytest.fixture()
def create_user(db_session):
    """Створює одного користувача з унікальним email"""
    unique_email = f"user_{uuid.uuid4().hex}@example.com"
    user = User(
        username="artur4ik",
        email=unique_email,
        password="123456789",
        avatar="url-avatar",
        is_verify=True,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture()
def create_posts(db_session, create_user):
    """Створює 3 пости для користувача"""
    posts = []
    for i in range(3):
        post = Post(
            title=f"Post {i}",
            descr=f"Body {i}",
            created_at=datetime.utcnow(),
            user_id=create_user.id,
            public_id=f"public_id_{i}"
        )
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)
        posts.append(post)
    return posts

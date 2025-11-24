import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connect_db import Base, get_db
from app.database.models import User, Post, Hashtag
from app.main import app
from datetime import datetime
import uuid


# -----------------------------
# Тестова база даних (in-memory)
# -----------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------
# Створення/видалення таблиць перед/після тестів
# -----------------------------
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# -----------------------------
# Тестова сесія DB
# -----------------------------
@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# -----------------------------
# FastAPI TestClient
# -----------------------------
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

# -----------------------------
# Тестовий користувач
# -----------------------------
@pytest.fixture()
def create_user(db_session):
    user = User(
        username="test_user",
        email=f"user_{uuid.uuid4().hex}@example.com",
        password="123456",
        avatar="url-avatar",
        is_verify=True,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# -----------------------------
# Тестові пости
# -----------------------------
@pytest.fixture()
def create_posts(db_session, create_user):
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
        db_session.flush()  # швидше ніж commit на кожному циклі
        posts.append(post)
    db_session.commit()  # commit всіх постів одночасно
    return posts

@pytest.fixture
def clean_db(db_session):
    """
    Очищає основні таблиці перед тестом.
    """
    db_session.query(Hashtag).delete()
    db_session.query(Transformation).delete()
    db_session.query(User).delete()
    db_session.commit()


@pytest.fixture
def user(db_session, clean_db):
    """
    Створює тестового користувача.
    """
    test_user = User(username="testuser", email="test@example.com")
    db_session.add(test_user)
    db_session.commit()
    return test_user


@pytest.fixture
def create_transformation(db_session, user):
    """
    Створює тестову трансформацію, пов’язану з користувачем.
    """
    # Очистка таблиці Transformation перед тестом
    db_session.query(Transformation).delete()
    db_session.commit()

    transformation = Transformation(title="example", user_id=user.id)
    db_session.add(transformation)
    db_session.commit()
    return transformation


@pytest.fixture
def create_hashtag(db_session):
    """
    Створює тестовий хештег.
    """
    # Очистка таблиці Hashtag перед тестом
    db_session.query(Hashtag).delete()
    db_session.commit()

    hashtag = Hashtag(name="example")
    db_session.add(hashtag)
    db_session.commit()
    return hashtag
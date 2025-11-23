import io
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest
from app.database.connect_db import Base, engine, SessionLocal
from app.database.models import User, UserRoleEnum
from app.repository import users as repository_users
from app.schemas import UserModel
from app.conf.messages import (
    ALREADY_EXISTS,
    EMAIL_NOT_CONFIRMED,
    INVALID_PASSWORD,
    INVALID_EMAIL,
    USER_NOT_ACTIVE,
    NOT_FOUND,
    OPERATION_FORBIDDEN,
    USER_ALREADY_NOT_ACTIVE,
    USER_ROLE_EXISTS,
    USER_CHANGE_ROLE_TO,
)
from app.services.auth import auth_service


# -------------------- DB Setup --------------------
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# -------------------- Fixtures --------------------
@pytest.fixture()
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def new_user(session):
    user_email = "artur4ik@example.com"
    db_user = session.query(User).filter(User.email == user_email).first()
    if not db_user:
        db_user = User(
            email=user_email,
            username="artur4ik",
            password="password123",
            avatar="url-avatar",
            role="admin",
            is_active=True,
            is_verify=True
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user

@pytest.fixture()
def second_user(session):
    db_user = session.query(User).filter(User.email == "second_user@example.com").first()
    if not db_user:
        db_user = User(
            username='second_user',
            email='second_user@example.com',
            password='qweqwe123123',
            role='user'
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user

@pytest.fixture()
def mock_redis():
    with patch.object(auth_service, 'redis_cache') as r_mock:
        r_mock.get.return_value = None
        yield r_mock

@pytest.fixture()
def token(client, new_user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("app.routes.auth.send_email", mock_send_email)
    new_user.is_verify = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": new_user.email, "password": "password123"}
    )
    return response.json()["access_token"]

# -------------------- Helpers --------------------
def make_admin(session, email):
    user = session.query(User).filter(User.email == email).first()
    user.role = "admin"
    session.commit()
    return user

# -------------------- Repository Tests --------------------
@pytest.mark.asyncio
async def test_get_me_repo(new_user, session):
    response = await repository_users.get_me(new_user, session)
    assert response.username == "artur4ik"
    assert response.email == "artur4ik@example.com"

@pytest.mark.asyncio
async def test_get_users_repo(new_user, second_user, session):
    response = await repository_users.get_users(0, 100, session)
    assert isinstance(response, list)
    assert len(response) >= 2  # може бути більше, залежно від попередніх тестів

@pytest.mark.asyncio
async def test_get_users_with_username_repo(new_user, session):
    response = await repository_users.get_users_with_username("artur", session)
    assert isinstance(response, list)
    assert response[0].username == "artur4ik"
    assert response[0].email == "artur4ik@example.com"

@pytest.mark.asyncio
async def test_get_user_profile_repo(new_user, session):
    response = await repository_users.get_user_profile("artur4ik", session)
    assert response.username == "artur4ik"
    assert response.email == "artur4ik@example.com"

@pytest.mark.asyncio
async def test_get_all_commented_posts_repo(new_user, session):
    response = await repository_users.get_all_commented_posts(new_user, session)
    assert isinstance(response, list)
    assert len(response) == 0

@pytest.mark.asyncio
async def test_get_all_liked_posts_repo(new_user, session):
    response = await repository_users.get_all_liked_posts(new_user, session)
    assert isinstance(response, list)
    assert len(response) == 0

@pytest.mark.asyncio
async def test_get_user_by_email_repo(second_user, session):
    response = await repository_users.get_user_by_email("second_user@example.com", session)
    assert response.username == "second_user"
    assert response.email == "second_user@example.com"

@pytest.mark.asyncio
async def test_create_user_repo(session):
    test_user = UserModel(
        username="test_user",
        email="test_user@example.com",
        password="123456789",
        avatar="url-avatar"
    )
    response = await repository_users.create_user(test_user, session)
    assert response.username == "test_user"
    assert response.email == "test_user@example.com"

@pytest.mark.asyncio
async def test_confirmed_email_repo(second_user, session):
    await repository_users.confirmed_email("second_user@example.com", session)
    updated_user = await repository_users.get_user_by_email("second_user@example.com", session)
    assert updated_user.is_verify

@pytest.mark.asyncio
async def test_ban_user_repo(second_user, session):
    await repository_users.ban_user("second_user@example.com", session)
    updated_user = await repository_users.get_user_by_email("second_user@example.com", session)
    assert not updated_user.is_active

@pytest.mark.asyncio
async def test_make_user_role_repo(second_user, session):
    await repository_users.make_user_role("second_user@example.com", "moder", session)
    updated_user = await repository_users.get_user_by_email("second_user@example.com", session)
    assert updated_user.role == UserRoleEnum.moder

# -------------------- API Endpoint Tests --------------------
def test_get_user_profile(client, create_user):
    response = client.get(f"/api/users/{create_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == create_user.id

def test_get_all_users(client, create_user):
    response = client.get("/api/users/all/")
    assert response.status_code == 200
    data = response.json()
    assert any(u["id"] == create_user.id for u in data)

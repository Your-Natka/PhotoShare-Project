import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, Mock, patch

from app.main import app
from app.conf.messages import (
    ALREADY_EXISTS, EMAIL_NOT_CONFIRMED, INVALID_PASSWORD, USER_NOT_ACTIVE,
    USER_IS_LOGOUT, EMAIL_CONFIRMED, CHECK_YOUR_EMAIL, SUCCESS_CREATE_USER
)
from app.services import auth as auth_service_module
from datetime import datetime



# ----------------- FIXED MOCK USER -----------------
def get_fake_user(**kwargs):
    user = Mock()
    user.id = kwargs.get("id", 1)
    user.username = kwargs.get("username", "testuser")
    user.email = kwargs.get("email", "test@example.com")
    user.avatar = kwargs.get("avatar", None)
    user.role = kwargs.get("role", "user")
    user.created_at = kwargs.get("created_at", datetime.now())
    user.is_verify = kwargs.get("is_verify", True)
    user.is_active = kwargs.get("is_active", True)
    user.password = kwargs.get("password", "hashed")
    user.refresh_token = kwargs.get("refresh_token", "refreshtoken")
    return user


@pytest.fixture
async def ac():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


# ----------------- SIGNUP -----------------
@pytest.mark.asyncio
async def test_signup_user_success(ac):  # ac = AsyncClient
    fake_user = get_fake_user()
    # Мокаємо метод create_user класу Auth
    with patch.object(auth_service_module.Auth, "create_user", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = fake_user
        
        response = await ac.post(
            "/api/auth/signup",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == fake_user.email
    assert data["username"] == fake_user.username


@pytest.mark.asyncio
async def test_signup_user_already_exists(ac):
    fake_user = get_fake_user()
    async def raise_exists(*args, **kwargs):
        return None 

    with patch.object(auth_service_module.Auth, "create_user", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = raise_exists

        response = await ac.post(
            "/api/auth/signup",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"] == "User already exists"

# ----------------- LOGIN -----------------
@pytest.mark.asyncio
async def test_login_success(monkeypatch):
    fake_user = get_fake_user()
    monkeypatch.setattr(auth_service_module.repository_users, "get_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(auth_service_module.auth_service, "verify_password", AsyncMock(return_value=True))
    monkeypatch.setattr(auth_service_module.auth_service, "create_access_token", AsyncMock(return_value="access123"))
    monkeypatch.setattr(auth_service_module.auth_service, "create_refresh_token", AsyncMock(return_value="refresh123"))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "test@example.com", "password": "any"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"] == "access123"
    assert data["refresh_token"] == "refresh123"

@pytest.mark.asyncio
async def test_login_not_verified(monkeypatch):
    fake_user = get_fake_user(is_verify=False)
    monkeypatch.setattr(auth_service_module.repository_users, "get_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(auth_service_module.auth_service, "verify_password", AsyncMock(return_value=True))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "test@example.com", "password": "any"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == EMAIL_NOT_CONFIRMED

@pytest.mark.asyncio
async def test_login_wrong_password(monkeypatch):
    fake_user = get_fake_user()
    monkeypatch.setattr(auth_service_module.repository_users, "get_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(auth_service_module.auth_service, "verify_password", lambda pw, hashed: False)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "test@example.com", "password": "wrong"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == INVALID_PASSWORD

@pytest.mark.asyncio
async def test_login_not_active(monkeypatch):
    fake_user = get_fake_user(is_active=False)
    monkeypatch.setattr(auth_service_module.repository_users, "get_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(auth_service_module.auth_service, "verify_password", AsyncMock(return_value=True))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "test@example.com", "password": "any"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == USER_NOT_ACTIVE

# ----------------- LOGOUT -----------------
@pytest.mark.asyncio
async def test_logout_success(monkeypatch):
    fake_user = get_fake_user()
    monkeypatch.setattr(auth_service_module.repository_users, "add_to_blacklist", AsyncMock())
    app.dependency_overrides[auth_service_module.auth_service.get_current_user] = lambda: fake_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/auth/logout", headers={"Authorization": "Bearer token"})

    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data["message"] == USER_IS_LOGOUT

    app.dependency_overrides = {}

# ----------------- REFRESH TOKEN -----------------
@pytest.mark.asyncio
async def test_refresh_token_success(monkeypatch):
    fake_user = get_fake_user(refresh_token="refreshtoken")
    monkeypatch.setattr(auth_service_module.auth_service, "decode_refresh_token", AsyncMock(return_value=fake_user.email))
    monkeypatch.setattr(auth_service_module.repository_users, "get_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(auth_service_module.repository_users, "update_token", AsyncMock())
    monkeypatch.setattr(auth_service_module.auth_service, "create_access_token", AsyncMock(return_value="newaccess"))
    monkeypatch.setattr(auth_service_module.auth_service, "create_refresh_token", AsyncMock(return_value="newrefresh"))

    app.dependency_overrides[auth_service_module.auth_service.get_current_user] = lambda: fake_user

    headers = {"Authorization": "Bearer refreshtoken"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/auth/refresh_token", headers=headers)

    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data["access_token"] == "newaccess"
    assert data["refresh_token"] == "newrefresh"

    app.dependency_overrides = {}

# ----------------- EMAIL CONFIRM -----------------
@pytest.mark.asyncio
async def test_confirmed_email_success(monkeypatch):
    fake_user = get_fake_user(is_verify=False)
    monkeypatch.setattr(auth_service_module.auth_service, "get_email_from_token", AsyncMock(return_value=fake_user.email))
    monkeypatch.setattr(auth_service_module.repository_users, "get_user_by_email", AsyncMock(return_value=fake_user))
    monkeypatch.setattr(auth_service_module.repository_users, "confirmed_email", AsyncMock())

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/auth/confirmed_email/testtoken")

    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data["message"] == EMAIL_CONFIRMED

# ----------------- REQUEST EMAIL -----------------
@pytest.mark.asyncio
async def test_request_email_success(ac):
    fake_user = get_fake_user()

    # Мокаємо метод send_email
    with patch.object(auth_service_module.Auth, "send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        # Мокаємо метод get_user_by_email, щоб повертав нашого фейкового юзера
        with patch.object(auth_service_module.Auth, "get_user_by_email", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = fake_user

            response = await ac.post(
                "/api/auth/request_email",
                json={"email": "test@example.com"}
            )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Email sent successfully"


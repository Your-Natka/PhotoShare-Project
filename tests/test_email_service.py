import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app
from app.services.auth import auth_service

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }

# ---------------------------------------------------------
# SIGNUP
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_register_user(client):
    """Тест реєстрації нового користувача"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    response = await client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_register_existing_email(monkeypatch, client, user_data):
    """Користувач з таким email вже існує"""

    monkeypatch.setattr(
        "app.repository.users.get_user_by_email",
        AsyncMock(return_value=True)
    )

    response = await client.post("/api/auth/signup", json=user_data)  # <- тут await
    assert response.status_code == 409
    assert response.json()["detail"] == "Account already exists."

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_login_user(monkeypatch, client, user_data):
    """Успішний логін"""

    fake_user = {
        "email": user_data["email"],
        "password": user_data["password"], 
        "is_verify": True,
        "is_active": True
    }

    monkeypatch.setattr(
        "app.repository.users.get_user_by_email",
        AsyncMock(return_value=fake_user)
    )

    monkeypatch.setattr(
        "app.repository.users.update_token",
        AsyncMock(return_value=True)
    )

    response = await client.post(
        "/api/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]}
    )

    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_login_wrong_password(monkeypatch, client, user_data):
    """Невірний пароль"""

    fake_user = {
        "email": user_data["email"],
        "password": "OTHER_PASSWORD",  # відмінний від введеного
        "is_verify": True,
        "is_active": True
    }

    monkeypatch.setattr(
        "app.repository.users.get_user_by_email",
        AsyncMock(return_value=fake_user)
    )

    response = await client.post(
        "/api/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password."


# ---------------------------------------------------------
# REFRESH TOKEN
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_token(monkeypatch, client, user_data):
    """Оновлення access та refresh токена"""
    fake_user = {
        "email": "test@example.com",
        "refresh_token": "OLD_REFRESH",
        "is_active": True,
        "is_verify": True
    }

    # repository mocks
    monkeypatch.setattr(
        "app.repository.users.get_user_by_email",
        AsyncMock(return_value=fake_user)
    )
    monkeypatch.setattr(
        "app.repository.users.update_token",
        AsyncMock(return_value=True)
    )

    # auth_service mocks
    monkeypatch.setattr(
        "app.services.auth.auth_service.decode_refresh_token",
        AsyncMock(return_value="test@example.com")
    )

    headers = {"Authorization": "Bearer OLD_REFRESH"}
    response = await client.get("/api/auth/refresh_token", headers=headers)

    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_logout(monkeypatch, client, user_data):
    """Тест логауту"""

    fake_user = {"email": "test@example.com"}

    monkeypatch.setattr(
        "app.services.auth.auth_service.get_current_user",
        AsyncMock(return_value=fake_user)
    )
    monkeypatch.setattr(
        "app.repository.users.add_to_blacklist",
        AsyncMock(return_value=True)
    )

    headers = {"Authorization": "Bearer TESTTOKEN"}

    response = await client.post("/api/auth/logout", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "User has been logged out."

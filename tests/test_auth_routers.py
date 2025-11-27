import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from fastapi import status
from app.main import app

# ---------------------------------------
# SIGNUP
# ---------------------------------------
@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
@patch("app.repository.users.create_user", new_callable=AsyncMock)
@patch("app.routers.auth.send_email", new_callable=AsyncMock)
async def test_register_user(mock_send_email, mock_create_user, mock_get_user):
    mock_get_user.return_value = None

    class MockUser:
        id = 1
        username = "testuser"
        email = "test@example.com"
        avatar = None
        role = "user"
        created_at = "2024-01-01"

    mock_create_user.return_value = MockUser()

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {"username": "testuser", "email": "test@example.com", "password": "12345678"}
        response = await ac.post("/api/auth/signup", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["detail"] == "User successfully created"
    mock_send_email.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
async def test_signup_existing_email(mock_get_user):
    mock_get_user.return_value = True
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {"username": "testuser", "email": "existing@example.com", "password": "12345678"}
        response = await ac.post("/api/auth/signup", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Account already exists."


# ---------------------------------------
# LOGIN
# ---------------------------------------
@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
@patch("app.repository.users.update_token", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.create_access_token", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.create_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.verify_password", new_callable=AsyncMock)
async def test_login_user(mock_verify, mock_refresh, mock_access, mock_update_token, mock_get_user):
    class User:
        email = "test@example.com"
        password = "hashed"
        is_verify = True
        is_active = True
        refresh_token = None

    mock_get_user.return_value = User()
    mock_access.return_value = "access123"
    mock_refresh.return_value = "refresh123"
    mock_verify.return_value = True

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/api/auth/login", data={"username": "test@example.com", "password": "12345678"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "access123"
    assert data["refresh_token"] == "refresh123"


@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
async def test_login_user_invalid_email(mock_get_user):
    mock_get_user.return_value = None
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/api/auth/login", data={"username": "wrong@example.com", "password": "123"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email."


@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.verify_password", new_callable=AsyncMock)
async def test_login_user_wrong_password(mock_verify, mock_get_user):
    class User:
        email = "test@example.com"
        password = "hashed"
        is_verify = True
        is_active = True
    mock_get_user.return_value = User()
    mock_verify.return_value = False

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/api/auth/login", data={"username": "test@example.com", "password": "wrong"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid password."


# ---------------------------------------
# REFRESH TOKEN
# ---------------------------------------
@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
@patch("app.repository.users.update_token", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.decode_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.create_access_token", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.create_refresh_token", new_callable=AsyncMock)
async def test_refresh_token(mock_create_refresh, mock_create_access, mock_decode, mock_update_token, mock_get_user):
    class User:
        email = "test@example.com"
        refresh_token = "refresh123"

    mock_decode.return_value = "test@example.com"
    mock_get_user.return_value = User()
    mock_create_access.return_value = "new_access"
    mock_create_refresh.return_value = "new_refresh"

    headers = {"Authorization": "Bearer refresh123"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/api/auth/refresh_token", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "new_access"
    assert data["refresh_token"] == "new_refresh"


@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.decode_refresh_token", new_callable=AsyncMock)
@patch("app.repository.users.update_token", new_callable=AsyncMock)
async def test_refresh_token_invalid(mock_update_token, mock_decode, mock_get_user):
    class User:
        email = "test@example.com"
        refresh_token = "OLD_REFRESH"

    mock_get_user.return_value = User()
    mock_decode.return_value = "test@example.com"

    headers = {"Authorization": "Bearer INVALID_TOKEN"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/api/auth/refresh_token", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token."


# ---------------------------------------
# LOGOUT
# ---------------------------------------
@pytest.mark.asyncio
@patch("app.repository.users.add_to_blacklist", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.get_current_user", new_callable=AsyncMock)
async def test_logout(mock_current_user, mock_blacklist):
    class User:
        email = "test@example.com"
    mock_current_user.return_value = User()

    headers = {"Authorization": "Bearer access123"}
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/api/auth/logout", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] in ["User successfully logged out", "USER_IS_LOGOUT"]
    mock_blacklist.assert_awaited_once()


# ---------------------------------------
# CONFIRM EMAIL
# ---------------------------------------
@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
@patch("app.services.auth.auth_service.get_email_from_token", new_callable=AsyncMock)
async def test_confirmed_email_failure(mock_get_email, mock_get_user):
    mock_get_email.return_value = "unknown@example.com"
    mock_get_user.return_value = None

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/api/auth/confirmed_email/FAKE_TOKEN")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Verification error"


# ---------------------------------------
# REQUEST EMAIL
# ---------------------------------------
@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
async def test_request_email_not_found(mock_get_user):
    mock_get_user.return_value = None
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/api/auth/request_email", json={"email": "unknown@example.com"})
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.repository.users.get_user_by_email", new_callable=AsyncMock)
async def test_request_email_already_confirmed(mock_get_user):
    class User:
        email = "test@example.com"
        is_verify = True
        username = "user"
    mock_get_user.return_value = User()

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post("/api/auth/request_email", json={"email": "test@example.com"})

    assert response.status_code == 200
    assert response.json()["message"] == "Email already confirmed"

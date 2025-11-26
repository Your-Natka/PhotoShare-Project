import pytest
from unittest.mock import AsyncMock, patch
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.services.auth import Auth
from app.conf.messages import FAIL_EMAIL_VERIFICATION

auth_service = Auth()


# ---------------- Password hashing ---------------- #
def test_password_hashing_and_verification():
    password = "mysecretpassword"
    hashed = auth_service.get_password_hash(password)
    assert auth_service.verify_password(password, hashed) is True
    assert auth_service.verify_password("wrongpassword", hashed) is False


# ---------------- Access token ---------------- #
@pytest.mark.asyncio
async def test_create_and_decode_access_token():
    data = {"sub": "user@example.com"}
    token = await auth_service.create_access_token(data)
    decoded = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert decoded["scope"] == "access_token"
    assert "exp" in decoded
    assert "iat" in decoded


# ---------------- Refresh token ---------------- #
@pytest.mark.asyncio
async def test_create_and_decode_refresh_token():
    data = {"sub": "user@example.com"}
    token = await auth_service.create_refresh_token(data)
    decoded = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert decoded["scope"] == "refresh_token"


# ---------------- Email token ---------------- #
def test_create_and_decode_email_token():
    data = {"sub": "user@example.com"}
    token = auth_service.create_email_token(data)
    decoded = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert decoded["scope"] == "email_token"


# ---------------- get_current_user ---------------- #
@pytest.mark.asyncio
@patch("app.services.auth.repository_users.get_user_by_email", new_callable=AsyncMock)
@patch("app.services.auth.repository_users.find_blacklisted_token", new_callable=AsyncMock)
async def test_get_current_user(mock_blacklist, mock_get_user):
    auth = Auth()
    auth.redis_cache = AsyncMock()

    email = "user@example.com"
    now = datetime.now(timezone.utc)
    token_data = {
        "sub": email,
        "scope": "access_token",
        "iat": now,
        "exp": now + timedelta(minutes=15)
    }
    token = jwt.encode(token_data, auth.SECRET_KEY, algorithm=auth.ALGORITHM)

    user_obj = {"email": email, "username": "user1"}
    mock_get_user.return_value = user_obj
    mock_blacklist.return_value = False
    auth.redis_cache.get.return_value = None

    user = await auth.get_current_user(token=token, db=None)
    assert user == user_obj
    auth.redis_cache.set.assert_called_once()


# ---------------- get_email_from_token ---------------- #
@pytest.mark.asyncio
async def test_get_email_from_token_invalid_scope():
    # Створюємо email токен
    token = auth_service.create_email_token({"sub": "user@example.com"})

    # Декодуємо, змінюємо scope на неправильний
    payload = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
    payload["scope"] = "wrong_scope"
    wrong_token = jwt.encode(payload, auth_service.SECRET_KEY, algorithm=auth_service.ALGORITHM)

    # Викликаємо метод і очікуємо HTTPException
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.get_email_from_token(wrong_token)

    assert exc_info.value.status_code == 401
    assert FAIL_EMAIL_VERIFICATION in str(exc_info.value.detail)

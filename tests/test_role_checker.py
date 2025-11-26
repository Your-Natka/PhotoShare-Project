import pytest
from fastapi import HTTPException

from app.database.models import User, UserRoleEnum
from app.services.auth import auth_service
from app.services.roles import RoleChecker

@pytest.mark.asyncio
async def test_role_checker_allows_access(monkeypatch):
    """
    Доступ дозволено, якщо роль користувача входить у allowed_roles.
    """
    # Фейковий користувач з роллю admin
    fake_user = User(role=UserRoleEnum.admin)

    # Мокаємо auth_service.get_current_user, щоб повертати реального користувача
    async def mock_get_user():
        return fake_user

    monkeypatch.setattr(auth_service, "get_current_user", mock_get_user)

    checker = RoleChecker(allowed_roles=[UserRoleEnum.admin])  # allowed_roles = список ролей

    # Виклик __call__ з передачею користувача через мок
    result = await checker(current_user=fake_user)
    assert result is True


@pytest.mark.asyncio
async def test_role_checker_denies_access(monkeypatch):
    """
    Доступ заборонено, якщо роль користувача НЕ входить у allowed_roles.
    """
    fake_user = User(role=UserRoleEnum.user)

    async def mock_get_user():
        return fake_user

    monkeypatch.setattr(auth_service, "get_current_user", mock_get_user)

    checker = RoleChecker(allowed_roles=[UserRoleEnum.admin])

    # Викликаємо і очікуємо HTTPException
    with pytest.raises(HTTPException) as exc:
        await checker(current_user=fake_user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Operation forbidden"

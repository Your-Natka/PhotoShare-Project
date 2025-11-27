import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import pytest_asyncio


class Obj:
    def __init__(self, **entries):
        self.__dict__.update(entries)

# --------------------------------------
# MOCK DATABASE SESSION
# --------------------------------------
class FakeAsyncSession:
    def __init__(self):
        self.users = []

    async def execute(self, query):
        # Проста емулююча функція для select
        class Result:
            def scalar_one_or_none(inner_self):
                if self.users:
                    return self.users[0]
                return None
        return Result()

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def close(self):
        pass

# --------------------------------------
# FIXTURE ASYNC CLIENT
# --------------------------------------

@pytest_asyncio.fixture
async def client_fixture():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# --------------------------------------
# MOCK REDIS
# --------------------------------------
@pytest.fixture(autouse=True)
def mock_redis():
    with patch("app.main.redis.from_url") as mock_redis:
        mock_instance = AsyncMock()
        mock_instance.ping.return_value = True
        mock_redis.return_value = mock_instance
        yield mock_redis

# --------------------------------------
# MOCK DATABASE
# --------------------------------------
@pytest.fixture(autouse=True)
def mock_db():
    with patch("app.routers.auth.get_db") as mock:
        session = FakeAsyncSession()
        mock.return_value = session
        yield mock

# --------------------------------------
# TESTS
# --------------------------------------

@pytest.mark.asyncio
async def test_register_user(client_fixture):
    with patch("app.repository.users.get_user_by_email",
               new_callable=AsyncMock) as mock_get:

        mock_get.return_value = None  # користувача не існує

        with patch("app.services.auth.auth_service.get_password_hash",
                   return_value="hashed_password"):

            with patch("app.repository.users.create_user",
                       new_callable=AsyncMock) as mock_create:

                
                mock_create.return_value = Obj(
                    id=1,
                    username="user1",
                    email="user1@example.com",
                    password="hashed_password",
                    avatar=None,            
                    role="User",            
                    created_at="2025-01-01T00:00:00"  
                )

                response = await client_fixture.post(
                    "/api/auth/signup",
                    json={
                        "username": "user1",
                        "email": "user1@example.com",
                        "password": "password123"
                    }
                )

    assert response.status_code in (200, 201)
    data = response.json()

    assert data["user"]["email"] == "user1@example.com"
    assert data["user"]["username"] == "user1"



@pytest.mark.asyncio
async def test_login_user(client_fixture):
    with patch("app.repository.users.get_user_by_email",
               new_callable=AsyncMock) as mock_get:

        mock_get.return_value = Obj(
            id=1,
            email="user1@example.com",
            username="user1",   
            password="hashed_password",
            is_active=True,
            is_verify=True
        )

        with patch("app.services.auth.auth_service.verify_password",
                   return_value=True):

            with patch("app.services.auth.auth_service.create_access_token",
                       return_value="access_token"):

                with patch("app.services.auth.auth_service.create_refresh_token",
                           return_value="refresh_token"):

                    with patch("app.repository.users.update_token",
                               new_callable=AsyncMock):

                        response = await client_fixture.post(
                            "/api/auth/login",
                            data={
                                "username": "user1@example.com",
                                "password": "password123"
                            }
                        )

    assert response.status_code in (200, 201)
    data = response.json()

    assert data["access_token"] == "access_token"
    assert data["refresh_token"] == "refresh_token"
    assert data["token_type"] == "bearer"

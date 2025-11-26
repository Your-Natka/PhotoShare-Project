import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.database.models import User
from app.database.connect_db import get_db

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
@pytest.fixture
async def client_fixture():
    from httpx import AsyncClient
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
    with patch("app.routes.auth.get_db") as mock:
        session = FakeAsyncSession()
        mock.return_value = session
        yield mock

# --------------------------------------
# TESTS
# --------------------------------------
@pytest.mark.asyncio
async def test_register_user(client_fixture):
    response = await client_fixture.post("/api/auth/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123"
    })
    assert response.status_code in (201, 200)

@pytest.mark.asyncio
async def test_login_user(client_fixture):
    response = await client_fixture.post("/api/auth/login", json={
        "email": "user1@example.com",
        "password": "password123"
    })
    assert response.status_code in (201, 409)

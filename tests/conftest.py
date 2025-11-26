import pytest
from unittest.mock import AsyncMock, patch
from app.database.connect_db import get_db

# --------------------------------------
# MOCK ASYNC DB SESSION
# --------------------------------------
class FakeQuery:
    def __init__(self, users):
        self._users = users

    def filter(self, condition):
        # Проста перевірка на email
        self._users = [u for u in self._users if getattr(u, "email", None) == condition.right.value]
        return self

    def first(self):
        return self._users[0] if self._users else None

    def count(self):
        return len(self._users)

class FakeAsyncSession:
    def __init__(self):
        self.users = []

    def query(self, model):
        return FakeQuery(self.users)

    async def add(self, obj):
        self.users.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

@pytest.fixture
def fake_db():
    return FakeAsyncSession()

# --------------------------------------
# FIXTURE ASYNC CLIENT
# --------------------------------------
@pytest.fixture
async def client():
    from httpx import AsyncClient
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

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
    with patch("app.database.connect_db.get_db", return_value=FakeAsyncSession()):
        yield

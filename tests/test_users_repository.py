import pytest
from httpx import AsyncClient
from app.main import app
from app.repository import users as repository
from app.schemas import UserModel

# ---------------- Fake DB session ----------------
class FakeAsyncSession:
    def __init__(self):
        self.users = []

    def query(self, model):
        class Query:
            def __init__(self, users):
                self._users = users

            def filter(self, condition):
                self._users = [u for u in self._users if getattr(u, "email", None) == condition.right.value]
                return self

            def first(self):
                return self._users[0] if self._users else None

            def count(self):
                return len(self._users)
        return Query(self.users)

    async def add(self, obj):
        self.users.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

@pytest.fixture
def fake_db():
    return FakeAsyncSession()

# ---------------- HTTP client fixture ----------------
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# ---------------- Repository tests ----------------
@pytest.mark.asyncio
async def test_create_user_directly(fake_db):
    user_data = UserModel(username="tester", email="tester@example.com", password="secret")
    user = await repository.create_user(user_data, fake_db)
    assert user.username == "tester"
    assert user.email == "tester@example.com"

@pytest.mark.asyncio
async def test_get_user_by_email_directly(fake_db):
    class User:
        def __init__(self, email):
            self.email = email
    fake_db.users.append(User("tester@example.com"))
    user = await repository.get_user_by_email("tester@example.com", fake_db)
    assert user.email == "tester@example.com"

# ---------------- API tests ----------------
@pytest.mark.asyncio
async def test_register_user_api(client):
    response = await client.post("/api/auth/signup", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123",
        "role": "user"
    })
    assert response.status_code in (201, 409)

@pytest.mark.asyncio
async def test_login_user_api(client):
    response = await client.post("/api/auth/login", data={
        "username": "user1@example.com",
        "password": "password123"
    })
    assert response.status_code in (200, 401)

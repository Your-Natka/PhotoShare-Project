import pytest
from httpx import AsyncClient
from io import BytesIO
from app.main import app
from app.database.models import User, UserRoleEnum
from unittest.mock import MagicMock

# ------------------------------
# Fixture для AsyncClient + мок користувача
# ------------------------------
@pytest.fixture
async def client():
    async def fake_current_user():
        return User(id=1, username="tester", role=UserRoleEnum.user)

    app.dependency_overrides = {}
    app.dependency_overrides["auth_service.get_current_user"] = fake_current_user

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

# ------------------------------
# Тести CREATE POST
# ------------------------------
@pytest.mark.asyncio
async def test_create_new_post(client):
    # Тепер client — це async generator, треба "витягти" AsyncClient через async with
    async for ac in client:
        response = await ac.post(
            "/api/posts/new/",
            data={"title": "Test", "descr": "Desc", "hashtags": "tag1"},
            files={"file": ("test.txt", BytesIO(b"content"))}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["hashtags"] == ["tag1"]

@pytest.mark.asyncio
async def test_create_new_post_too_many_hashtags(client):
    response = await client.post(
        "/api/posts/new/",
        data=[("title", "Test"), ("descr", "Desc")] + [("hashtags", f"t{i}") for i in range(6)],
        files={"file": ("test.txt", BytesIO(b"content"))}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "You can only add up to 5 hashtags per post"

# ------------------------------
# Тести READ POSTS
# ------------------------------
@pytest.mark.asyncio
async def test_read_all_user_posts(client):
    async def fake_get_my_posts(skip, limit, user, db):
        post = MagicMock(id=1, title="Post", descr="Desc", hashtags=["tag"])
        return [post]

    from app.routers import posts
    posts.repository_posts.get_my_posts = fake_get_my_posts

    response = await client.get("/api/posts/my_posts")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == "Post"

@pytest.mark.asyncio
async def test_read_all_user_posts_404(client):
    async def fake_get_my_posts(skip, limit, user, db):
        return []

    from app.routers import posts
    posts.repository_posts.get_my_posts = fake_get_my_posts

    response = await client.get("/api/posts/my_posts")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_read_post_by_id(client):
    async def fake_get_post_by_id(post_id, user, db):
        return MagicMock(id=1, title="Title", descr="Desc", hashtags=["tag"])

    from app.routers import posts
    posts.repository_posts.get_post_by_id = fake_get_post_by_id

    response = await client.get("/api/posts/by_id/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Title"

@pytest.mark.asyncio
async def test_read_post_by_id_404(client):
    async def fake_get_post_by_id(post_id, user, db):
        return None

    from app.routers import posts
    posts.repository_posts.get_post_by_id = fake_get_post_by_id

    response = await client.get("/api/posts/by_id/999")
    assert response.status_code == 404

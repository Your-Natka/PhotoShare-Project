import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_post(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "username": "poster",
        "email": "poster@example.com",
        "password": "password123"
    })

    login = await client.post("/api/auth/login", data={
        "username": "poster",
        "password": "password123"
    })
    token = login.json()["access_token"]

    response = await client.post(
        "/api/posts/",
        json={"title": "My Post", "content": "Hello world"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Post"
    assert data["content"] == "Hello world"


@pytest.mark.asyncio
async def test_get_posts(client: AsyncClient):
    response = await client.get("/api/posts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

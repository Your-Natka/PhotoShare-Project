import pytest
from unittest.mock import AsyncMock
from fastapi import status
from httpx import AsyncClient
from datetime import datetime

from app.main import app
from app.schemas import HashtagBase, HashtagResponse
from app.database.models import User

@pytest.mark.asyncio
async def test_create_tag(mocker):
    mock_user = User(id=1, role="user")
    mock_db = AsyncMock()

    mock_tag = HashtagResponse(id=1, title="TestTag", user_id=1)
    mocker.patch(
        "app.repository.hashtags.create_tag",
        new_callable=AsyncMock,
        return_value=mock_tag
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/hashtags/new/", json={"title": "TestTag"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "TestTag"


@pytest.mark.asyncio
async def test_read_my_tags(mocker):
    mock_user = User(id=1, role="user")
    mock_db = AsyncMock()

    mock_tags = [
        HashtagResponse(id=1, title="Tag1", user_id=1),
        HashtagResponse(id=2, title="Tag2", user_id=1)
    ]
    mocker.patch(
        "app.repository.hashtags.get_my_tags",
        new_callable=AsyncMock,
        return_value=mock_tags
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/hashtags/my/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_read_tag_by_id_found(mocker):
    mock_tag = HashtagResponse(id=1, title="Tag1", user_id=1)
    mocker.patch(
        "app.repository.hashtags.get_tag_by_id",
        new_callable=AsyncMock,
        return_value=mock_tag
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/hashtags/by_id/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Tag1"


@pytest.mark.asyncio
async def test_read_tag_by_id_not_found(mocker):
    mocker.patch(
        "app.repository.hashtags.get_tag_by_id",
        new_callable=AsyncMock,
        return_value=None
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/hashtags/by_id/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_tag_found(mocker):
    mock_tag = HashtagResponse(id=1, title="UpdatedTag", user_id=1)
    mocker.patch(
        "app.repository.hashtags.update_tag",
        new_callable=AsyncMock,
        return_value=mock_tag
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/api/hashtags/upd_tag/1", json={"title": "UpdatedTag"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "UpdatedTag"


@pytest.mark.asyncio
async def test_update_tag_not_found(mocker):
    mocker.patch(
        "app.repository.hashtags.update_tag",
        new_callable=AsyncMock,
        return_value=None
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/api/hashtags/upd_tag/999", json={"title": "NoTag"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_remove_tag_found(mocker):
    mock_tag = HashtagResponse(id=1, title="TagToRemove", user_id=1)
    mocker.patch(
        "app.repository.hashtags.remove_tag",
        new_callable=AsyncMock,
        return_value=mock_tag
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete("/api/hashtags/del/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "TagToRemove"


@pytest.mark.asyncio
async def test_remove_tag_not_found(mocker):
    mocker.patch(
        "app.repository.hashtags.remove_tag",
        new_callable=AsyncMock,
        return_value=None
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete("/api/hashtags/del/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND

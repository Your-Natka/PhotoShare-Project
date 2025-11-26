import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime
from app.main import app  # твій FastAPI app
from app.database.models import User
from app.schemas import CommentBase, CommentResponse 

mock_comment = CommentResponse(
    id=1,
    text="Comment",
    user_id=1,
    post_id=1,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

# ------------------------
# Фікстури
# ------------------------
@pytest.fixture
def mock_user():
    return User(id=1, role="user")

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db

@pytest.fixture
def comment_body():
    return CommentBase(text="Test comment")

# ------------------------
# Тести
# ------------------------
@pytest.mark.asyncio
async def test_create_comment(mocker, mock_user, mock_db, comment_body):
    # Мок функції repository
    mocker.patch(
        "app.repository.comments.create_comment",
        new_callable=AsyncMock,
        return_value=CommentResponse(id=1, text="Test comment", user_id=1, post_id=1)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/comments/new/1", json=comment_body.dict())

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["text"] == "Test comment"


@pytest.mark.asyncio
async def test_edit_comment(mocker, mock_user, mock_db, comment_body):
    mocker.patch(
        "app.repository.comments.edit_comment",
        new_callable=AsyncMock,
        return_value=CommentResponse(id=1, text="Updated comment", user_id=1, post_id=1)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/comments/edit/1", json=comment_body.dict())

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["text"] == "Updated comment"


@pytest.mark.asyncio
async def test_delete_comment(mocker, mock_user, mock_db):
    mocker.patch(
        "app.repository.comments.delete_comment",
        new_callable=AsyncMock,
        return_value=CommentResponse(id=1, text="To delete", user_id=1, post_id=1)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete("/comments/delete/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["text"] == "To delete"


@pytest.mark.asyncio
async def test_single_comment(mocker, mock_user, mock_db):
    mocker.patch(
        "app.repository.comments.show_single_comment",
        new_callable=AsyncMock,
        return_value=CommentResponse(id=1, text="Single comment", user_id=1, post_id=1)
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/comments/single/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["text"] == "Single comment"


@pytest.mark.asyncio
async def test_by_user_comments(mocker, mock_user, mock_db):
    mocker.patch(
        "app.repository.comments.show_user_comments",
        new_callable=AsyncMock,
        return_value=[
            CommentResponse(id=1, text="Comment 1", user_id=1, post_id=1),
            CommentResponse(id=2, text="Comment 2", user_id=1, post_id=2)
        ]
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/comments/by_author/1")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_by_user_post_comments(mocker, mock_user, mock_db):
    mocker.patch(
        "app.repository.comments.show_user_post_comments",
        new_callable=AsyncMock,
        return_value=[
            CommentResponse(id=1, text="Post comment", user_id=1, post_id=1)
        ]
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/comments/post_by_author/1/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["text"] == "Post comment"

@pytest.mark.asyncio
async def test_single_comment(mocker, mock_user, mock_db):
    mocker.patch(
        "app.repository.comments.show_single_comment",
        new_callable=AsyncMock,
        return_value=CommentResponse(
            id=1,
            text="Single comment",
            user_id=1,
            post_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/comments/single/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["text"] == "Single comment"


@pytest.mark.asyncio
async def test_by_user_comments(mocker, mock_user, mock_db):
    mocker.patch(
        "app.repository.comments.show_user_comments",
        new_callable=AsyncMock,
        return_value=[
            CommentResponse(
                id=1, text="Comment 1", user_id=1, post_id=1,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            ),
            CommentResponse(
                id=2, text="Comment 2", user_id=1, post_id=2,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
        ]
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/comments/by_author/1")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
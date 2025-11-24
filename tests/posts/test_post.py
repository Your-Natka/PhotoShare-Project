import io
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from fastapi import UploadFile
from PIL import Image

from app.database.models import User, Post
import app.repository.posts as repository_posts
from app.schemas import PostUpdate
from app.services.auth import auth_service
from app.conf.messages import NOT_FOUND

# ------------------- FIXTURES -------------------

@pytest.fixture()
def current_user(user, db_session):
    db_user = db_session.query(User).filter(User.email == user.get('email')).first()
    if not db_user:
        db_user = User(
            email=user.get('email'),
            username=user.get('username'),
            password=user.get('password')
        )
        db_session.add(db_user)
        db_session.commit()
        db_session.refresh(db_user)
    return db_user

@pytest.fixture()
def post(current_user, db_session):
    db_post = db_session.query(Post).first()
    if not db_post:
        db_post = Post(
            image_url="https://res.cloudinary.com/dybgf2pue/image/upload/c_fill,h_250,w_250/Dominic",
            title="cat",
            descr="pet",
            hashtags=["cat", "pet"],
            created_at=datetime.now(),
            user_id=current_user.id,
            public_id="Dominic",
            done=True
        )
        db_session.add(db_post)
        db_session.commit()
        db_session.refresh(db_post)
    return db_post

@pytest.fixture()
def body():
    return {
        "title": "other_post",
        "descr": "other_post",
        "hashtags": ["other_post"]
    }

@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("app.routes.auth.send_email", mock_send_email)
    client.post("/api/auth/signup", json=user)
    db_user = session.query(User).filter(User.email == user.get('email')).first()
    db_user.is_verify = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    return response.json()["access_token"]

# ------------------- HELPER -------------------

def create_image_file():
    file_data = io.BytesIO()
    image = Image.new('RGB', (100, 100), (255, 0, 0))
    image.save(file_data, 'jpeg')
    file_data.seek(0)
    return UploadFile(file=file_data, filename="test.jpg", content_type="image/jpeg")

# ------------------- REPOSITORY TESTS -------------------

@pytest.mark.asyncio
async def test_create_post_repo(current_user, session):
    file = create_image_file()
    response = await repository_posts.create_post(
        file=file,
        title="test_post",
        descr="test_post",
        hashtags=["test_post"],
        session=session,
        current_user=current_user
    )
    assert isinstance(response.image_url, str)
    assert response.title == "test_post"
    assert response.descr == "test_post"
    assert "test_post" in response.hashtags

@pytest.mark.asyncio
async def test_get_all_posts_repo(session):
    response = await repository_posts.get_all_posts(skip=0, limit=100, session=session)
    assert isinstance(response, list)
    assert len(response) >= 1

@pytest.mark.asyncio
async def test_update_post_repo(post, body, current_user, session):
    body_obj = PostUpdate(**body)
    response = await repository_posts.update_post(post.id, body_obj, current_user, session)
    assert response.title == body["title"]
    assert response.descr == body["descr"]
    assert body["hashtags"][0] in response.hashtags

@pytest.mark.asyncio
async def test_remove_post_repo(post, current_user, session):
    await repository_posts.remove_post(post.id, current_user, session)
    response = await repository_posts.get_post_by_id(post.id, current_user, session)
    assert response is None

# ------------------- API TESTS -------------------

def test_create_post_repo(db_session, create_user):
    from app.repository.posts import PostRepository
    repo = PostRepository()
    post_data = {"title": "New Post", "descr": "Desc", "user_id": create_user.id, "public_id": "abc123"}
    post = repo.create_post(post_data, db_session)
    assert post.id is not None
    assert post.title == "New Post"

def test_get_all_posts(client, create_posts):
    response = client.get("/api/posts/all/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(create_posts)

def test_get_post_by_id(client, create_posts):
    post = create_posts[0]
    response = client.get(f"/api/posts/{post.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post.id

def test_update_post_repo(db_session, create_posts):
    from app.repository.posts import PostRepository
    repo = PostRepository()
    post = create_posts[0]
    updated = repo.update_post(post.id, {"title": "Updated"}, db_session)
    assert updated.title == "Updated"

def test_delete_post_repo(db_session, create_posts):
    from app.repository.posts import PostRepository
    repo = PostRepository()
    post = create_posts[0]
    deleted = repo.remove_post(post.id, db_session)
    assert deleted.id == post.id

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO

from app.repository import posts
from app.database.models import User, Post, Hashtag, UserRoleEnum
from app.schemas import PostUpdate


# -------------------------
# Моки для DB та Cloudinary
# -------------------------
class FakeDBSession:
    def __init__(self):
        self.posts = []
        self.hashtags = []
        self.added = []
        self.deleted = []

    def query(self, model):
        mock = MagicMock()
        # filter().first() -> повертаємо перший елемент списку або None
        mock.filter.return_value.first.side_effect = lambda: self.posts[0] if self.posts else None
        # filter().all() -> повертаємо список
        mock.filter.return_value.all.side_effect = lambda: self.posts
        # join().filter().all() -> для хештегів
        mock.join.return_value.filter.return_value.all.side_effect = lambda: self.posts
        return mock

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def delete(self, obj):
        self.deleted.append(obj)


@pytest.fixture
def fake_db():
    return FakeDBSession()


@pytest.fixture
def fake_user():
    return User(id=1, username="tester", role=UserRoleEnum.user)


@pytest.fixture
def fake_upload_file():
    return UploadFile(filename="test.png", file=BytesIO(b"fake image data"))


# -------------------------
# Тести
# -------------------------
@pytest.mark.asyncio
@patch("app.repository.posts.cloudinary.uploader.upload")
async def test_create_post(mock_upload, fake_db, fake_user, fake_upload_file):
    # Мок завантаження зображення
    mock_upload.return_value = {"secure_url": "https://fakeurl.com/image.png"}

    result = await posts.create_post(
        request=None,
        title="Test Post",
        descr="Description",
        hashtags=["tag1,tag2"],
        file=fake_upload_file,
        db=fake_db,
        current_user=fake_user
    )

    assert isinstance(result, Post)
    assert result.title == "Test Post"
    assert result.user_id == fake_user.id
    assert result.hashtags  # перевіряємо що хештеги додались
    assert mock_upload.called


@pytest.mark.asyncio
async def test_get_all_posts(fake_db):
    posts_list = await posts.get_all_posts(skip=0, limit=10, db=fake_db)
    assert isinstance(posts_list, list)


@pytest.mark.asyncio
async def test_get_post_by_id(fake_db, fake_user):
    post = Post(id=1, title="Test", descr="Desc", user_id=fake_user.id)
    fake_db.posts.append(post)
    result = await posts.get_post_by_id(post_id=1, user=fake_user, db=fake_db)
    assert result == post


@pytest.mark.asyncio
@patch("app.repository.posts.cloudinary.uploader.destroy")
async def test_remove_post(mock_destroy, fake_db, fake_user):
    post = Post(id=1, title="Test", descr="Desc", user_id=fake_user.id, public_id="abc123")
    fake_db.posts.append(post)
    result = await posts.remove_post(post_id=1, user=fake_user, db=fake_db)
    assert result == post
    assert mock_destroy.called
    assert post in fake_db.deleted


@pytest.mark.asyncio
async def test_update_post(fake_db, fake_user):
    post = Post(id=1, title="Old", descr="Old desc", user_id=fake_user.id)
    fake_db.posts.append(post)
    body = PostUpdate(title="New", descr="New desc", hashtags=["tag1"])
    result = await posts.update_post(post_id=1, body=body, user=fake_user, db=fake_db)
    assert result.title == "New"
    assert result.descr == "New desc"
    assert result.hashtags

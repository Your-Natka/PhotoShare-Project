import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.repository import comments
from app.database.models import Comment, User, UserRoleEnum
from app.schemas import CommentBase

# -----------------------------
# Fake DB Session
# -----------------------------
class FakeDBSession:
    def __init__(self):
        self.comments = []
        self.added = []
        self.deleted = []

    def query(self, model):
        mock = MagicMock()
        # filter().all()
        mock.filter.return_value.all.side_effect = lambda: self.comments
        # filter().first()
        mock.filter.return_value.first.side_effect = lambda: self.comments[0] if self.comments else None
        return mock

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def delete(self, obj):
        self.deleted.append(obj)

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def fake_db():
    return FakeDBSession()

@pytest.fixture
def user():
    return User(id=1, username="tester", role=UserRoleEnum.user)

@pytest.fixture
def admin_user():
    return User(id=2, username="admin", role=UserRoleEnum.admin)

@pytest.fixture
def comment_obj(user):
    c = Comment(id=1, text="Hello", post_id=1, user_id=user.id)
    return c

# -----------------------------
# Tests
# -----------------------------
@pytest.mark.asyncio
async def test_create_comment(fake_db, user):
    body = CommentBase(text="New comment")
    comment = await comments.create_comment(post_id=1, body=body, db=fake_db, user=user)
    assert comment.text == "New comment"
    assert comment.user_id == user.id
    assert fake_db.added

@pytest.mark.asyncio
async def test_edit_comment_authorized(fake_db, user, comment_obj):
    fake_db.comments.append(comment_obj)
    body = CommentBase(text="Updated comment")
    updated = await comments.edit_comment(comment_id=1, body=body, db=fake_db, user=user)
    assert updated.text == "Updated comment"

@pytest.mark.asyncio
async def test_edit_comment_unauthorized(fake_db, comment_obj):
    fake_db.comments.append(comment_obj)
    other_user = User(id=3, username="other", role=UserRoleEnum.user)
    body = CommentBase(text="Updated comment")
    with pytest.raises(HTTPException):
        await comments.edit_comment(comment_id=1, body=body, db=fake_db, user=other_user)

@pytest.mark.asyncio
async def test_delete_comment_author(fake_db, user, comment_obj):
    fake_db.comments.append(comment_obj)
    result = await comments.delete_comment(comment_id=1, db=fake_db, user=user)
    assert result == comment_obj
    assert comment_obj in fake_db.deleted

@pytest.mark.asyncio
async def test_delete_comment_admin(fake_db, admin_user, comment_obj):
    fake_db.comments.append(comment_obj)
    result = await comments.delete_comment(comment_id=1, db=fake_db, user=admin_user)
    assert result == comment_obj
    assert comment_obj in fake_db.deleted

@pytest.mark.asyncio
async def test_show_single_comment_author(fake_db, user, comment_obj):
    fake_db.comments.append(comment_obj)
    result = await comments.show_single_comment(comment_id=1, db=fake_db, user=user)
    assert result == comment_obj

@pytest.mark.asyncio
async def test_show_single_comment_unauthorized(fake_db, comment_obj):
    fake_db.comments.append(comment_obj)
    other_user = User(id=3, username="other", role=UserRoleEnum.user)
    result = await comments.show_single_comment(comment_id=1, db=fake_db, user=other_user)
    assert result is None

@pytest.mark.asyncio
async def test_show_user_comments(fake_db, user, comment_obj):
    fake_db.comments.append(comment_obj)
    result = await comments.show_user_comments(user_id=user.id, db=fake_db)
    assert result == [comment_obj]

@pytest.mark.asyncio
async def test_show_user_post_comments(fake_db, user, comment_obj):
    fake_db.comments.append(comment_obj)
    result = await comments.show_user_post_comments(user_id=user.id, post_id=1, db=fake_db)
    assert result == [comment_obj]

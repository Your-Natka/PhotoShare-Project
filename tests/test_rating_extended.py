import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from starlette import status

from app.repository import ratings
from app.database.models import Rating, Post, User, UserRoleEnum
from app.conf import messages as message


# -----------------------------
# Fake DB Session
# -----------------------------
class FakeDB:
    def __init__(self):
        self.posts = []
        self.rates = []
        self.deleted = []
        self.added = []

    def query(self, model):
        mock = MagicMock()

        # -------- Пост --------
        if model is Post:
            # filter(Post.id == X).first()
            mock.filter.return_value.first.side_effect = lambda: (
                self.posts[0] if self.posts else None
            )

        # -------- Rating --------
        if model is Rating:
            # filter(...).first()
            mock.filter.return_value.first.side_effect = lambda: (
                self.rates[0] if self.rates else None
            )

            # all()
            mock.all.side_effect = lambda: self.rates

            # filter(...).all()
            mock.filter.return_value.all.side_effect = lambda: self.rates

        return mock

    def add(self, obj):
        self.added.append(obj)
        self.rates.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def delete(self, obj):
        self.deleted.append(obj)
        self.rates.remove(obj)


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def db():
    return FakeDB()

@pytest.fixture
def user():
    return User(id=1, username="john", role=UserRoleEnum.user)

@pytest.fixture
def admin():
    return User(id=2, username="admin", role=UserRoleEnum.admin)

@pytest.fixture
def post(user):
    return Post(id=10, user_id=user.id)

@pytest.fixture
def rate(user):
    return Rating(id=5, post_id=10, user_id=user.id, rate=1)


# -----------------------------
# TESTS
# -----------------------------

# ---- CREATE RATE ----
@pytest.mark.asyncio
async def test_create_rate_success(db, post, user):
    db.posts.append(Post(id=10, user_id=2))  # пост іншого користувача
    new_rate = await ratings.create_rate(post_id=10, rate=1, db=db, user=user)

    assert new_rate.post_id == 10
    assert new_rate.rate == 1
    assert new_rate.user_id == user.id
    assert db.added


@pytest.mark.asyncio
async def test_create_rate_self_post_error(db, post, user):
    db.posts.append(post)  # пост належить user

    with pytest.raises(HTTPException) as exc:
        await ratings.create_rate(10, 1, db, user)

    assert exc.value.status_code == status.HTTP_423_LOCKED
    assert exc.value.detail == message.OWN_POST


@pytest.mark.asyncio
async def test_create_rate_vote_twice_error(db, post, user, rate):
    db.posts.append(Post(id=10, user_id=2))  # нормальний пост
    db.rates.append(rate)  # користувач уже голосував

    with pytest.raises(HTTPException) as exc:
        await ratings.create_rate(10, 1, db, user)

    assert exc.value.status_code == status.HTTP_423_LOCKED
    assert exc.value.detail == message.VOTE_TWICE


# ---- EDIT RATE ----
@pytest.mark.asyncio
async def test_edit_rate_by_owner(db, user, rate):
    db.rates.append(rate)
    updated = await ratings.edit_rate(rate_id=5, new_rate=-1, db=db, user=user)

    assert updated.rate == -1


@pytest.mark.asyncio
async def test_edit_rate_by_admin(db, admin, rate):
    db.rates.append(rate)
    updated = await ratings.edit_rate(rate_id=5, new_rate=1, db=db, user=admin)

    assert updated.rate == 1


@pytest.mark.asyncio
async def test_edit_rate_not_found(db, user):
    updated = await ratings.edit_rate(rate_id=99, new_rate=1, db=db, user=user)
    assert updated is None


# ---- DELETE RATE ----
@pytest.mark.asyncio
async def test_delete_rate_success(db, rate):
    db.rates.append(rate)
    deleted = await ratings.delete_rate(rate_id=5, db=db, user=None)

    assert deleted == rate
    assert rate in db.deleted


@pytest.mark.asyncio
async def test_delete_rate_not_found(db):
    deleted = await ratings.delete_rate(rate_id=999, db=db, user=None)
    assert deleted is None


# ---- SHOW RATINGS ----
@pytest.mark.asyncio
async def test_show_ratings(db, rate):
    db.rates.append(rate)
    result = await ratings.show_ratings(db=db, user=None)

    assert result == [rate]


# ---- SHOW MY RATINGS ----
@pytest.mark.asyncio
async def test_show_my_ratings(db, user, rate):
    db.rates.append(rate)
    result = await ratings.show_my_ratings(db=db, user=user)

    assert result == [rate]


# ---- USER RATE POST ----
@pytest.mark.asyncio
async def test_user_rate_post(db, rate):
    db.rates.append(rate)
    result = await ratings.user_rate_post(user_id=1, post_id=10, db=db, user=None)

    assert result == rate


@pytest.mark.asyncio
async def test_user_rate_post_not_found(db):
    result = await ratings.user_rate_post(user_id=1, post_id=10, db=db, user=None)
    assert result is None

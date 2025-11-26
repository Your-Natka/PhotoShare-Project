import pytest
from unittest.mock import MagicMock
from app.repository import hashtags
from app.database.models import Hashtag, User
from app.schemas import HashtagBase

# -----------------------------
# Fake DB Session
# -----------------------------
class FakeDBSession:
    def __init__(self):
        self.tags = []
        self.added = []
        self.deleted = []

    def query(self, model):
        mock = MagicMock()
        # filter().all()
        mock.filter.return_value.all.side_effect = lambda: self.tags
        # filter().first()
        mock.filter.return_value.first.side_effect = lambda: self.tags[0] if self.tags else None
        # offset/limit chaining
        mock.filter.return_value.offset.return_value.limit.return_value.all.side_effect = lambda: self.tags
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
    return User(id=1, username="tester")

@pytest.fixture
def tag_obj(user):
    t = Hashtag(id=1, title="testtag", user_id=user.id)
    return t

# -----------------------------
# Tests
# -----------------------------
@pytest.mark.asyncio
async def test_create_tag_new(fake_db, user):
    body = HashtagBase(title="newtag")
    tag = await hashtags.create_tag(body=body, user=user, db=fake_db)
    assert tag.title == "newtag"
    assert tag.user_id == user.id
    assert fake_db.added

@pytest.mark.asyncio
async def test_create_tag_existing(fake_db, user, tag_obj):
    fake_db.tags.append(tag_obj)
    body = HashtagBase(title="testtag")
    tag = await hashtags.create_tag(body=body, user=user, db=fake_db)
    assert tag == tag_obj  # Повертає існуючий тег

@pytest.mark.asyncio
async def test_get_my_tags(fake_db, user, tag_obj):
    fake_db.tags.append(tag_obj)
    result = await hashtags.get_my_tags(skip=0, limit=10, user=user, db=fake_db)
    assert result == [tag_obj]

@pytest.mark.asyncio
async def test_get_all_tags(fake_db, tag_obj):
    fake_db.tags.append(tag_obj)
    result = await hashtags.get_all_tags(skip=0, limit=10, db=fake_db)
    assert result == [tag_obj]

@pytest.mark.asyncio
async def test_get_tag_by_id(fake_db, tag_obj):
    fake_db.tags.append(tag_obj)
    result = await hashtags.get_tag_by_id(tag_id=1, db=fake_db)
    assert result == tag_obj

@pytest.mark.asyncio
async def test_update_tag_existing(fake_db, tag_obj):
    fake_db.tags.append(tag_obj)
    body = HashtagBase(title="updated")
    result = await hashtags.update_tag(tag_id=1, body=body, db=fake_db)
    assert result.title == "updated"

@pytest.mark.asyncio
async def test_update_tag_not_found(fake_db):
    body = HashtagBase(title="updated")
    result = await hashtags.update_tag(tag_id=1, body=body, db=fake_db)
    assert result is None

@pytest.mark.asyncio
async def test_remove_tag_existing(fake_db, tag_obj):
    fake_db.tags.append(tag_obj)
    result = await hashtags.remove_tag(tag_id=1, db=fake_db)
    assert result == tag_obj
    assert tag_obj in fake_db.deleted

@pytest.mark.asyncio
async def test_remove_tag_not_found(fake_db):
    result = await hashtags.remove_tag(tag_id=1, db=fake_db)
    assert result is None

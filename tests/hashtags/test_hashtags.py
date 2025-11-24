import pytest
from unittest.mock import MagicMock
from app.database.models import Hashtag, User
from app.schemas import HashtagBase
from app.repository import hashtags  # твої функції: create_tag, get_my_tags тощо

# ========================
# ФІКСТУРИ
# ========================
@pytest.fixture
def fake_user():
    return User(id=1, username="testuser", email="test@example.com")

@pytest.fixture
def fake_hashtag():
    return Hashtag(id=1, title="dog", user_id=1)

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.query = MagicMock()
    db.delete = MagicMock()
    return db

# ========================
# РЕПОЗИТОРНІ ТЕСТИ
# ========================
@pytest.mark.asyncio
async def test_create_tag(mock_db, fake_user):
    # Мокаємо, що тег ще не існує
    mock_db.query().filter().first.return_value = None
    body = HashtagBase(title="dog")
    
    result = await hashtags.create_tag(body, fake_user, mock_db)

    assert result.title == "dog"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_remove_tag(mock_db, fake_hashtag):
    mock_db.query().filter().first.return_value = fake_hashtag
    
    result = await hashtags.remove_tag(1, mock_db)

    assert result == fake_hashtag
    mock_db.delete.assert_called_once_with(fake_hashtag)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_tag(mock_db, fake_hashtag):
    mock_db.query().filter().first.return_value = fake_hashtag
    body = HashtagBase(title="cat")

    result = await hashtags.update_tag(1, body, mock_db)

    assert result.title == "cat"
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_tag_by_id(mock_db, fake_hashtag):
    mock_db.query().filter().first.return_value = fake_hashtag

    result = await hashtags.get_tag_by_id(1, mock_db)

    assert result == fake_hashtag

@pytest.mark.asyncio
async def test_get_my_tags(mock_db, fake_hashtag, fake_user):
    mock_db.query().filter().offset().limit().all.return_value = [fake_hashtag]

    result = await hashtags.get_my_tags(skip=0, limit=10, user=fake_user, db=mock_db)

    assert result == [fake_hashtag]

@pytest.mark.asyncio
async def test_get_all_tags(mock_db, fake_hashtag):
    mock_db.query().offset().limit().all.return_value = [fake_hashtag]

    result = await hashtags.get_all_tags(skip=0, limit=10, db=mock_db)

    assert result == [fake_hashtag]



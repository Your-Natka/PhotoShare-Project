import pytest
from datetime import datetime
from app.database.models import User, Hashtag
from app.repository import hashtags as repository_tag
from app.schemas import HashtagBase
from app.database.connect_db import SessionLocal, Base, engine

# -------------------- DB Setup --------------------
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# -------------------- Fixtures --------------------
@pytest.fixture()
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def new_user(session):
    email = "artur4ik@example.com"
    user = session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username="artur4ik",
            password="password123",
            is_verify=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

@pytest.fixture()
def tag(new_user, session):
    db_tag = session.query(Hashtag).first()
    if not db_tag:
        db_tag = Hashtag(
            title="dog",
            user_id=new_user.id,
            created_at=datetime.utcnow()
        )
        session.add(db_tag)
        session.commit()
        session.refresh(db_tag)
    return db_tag

# -------------------- Repository Tests --------------------
def test_create_tag_repo(tag, new_user, session):
    body = HashtagBase(title="dog")
    response = repository_tag.create_tag(body, new_user, session)
    assert response.title == "dog"
    assert response.user_id == new_user.id

def test_get_my_tags_repo(new_user, session):
    tags = repository_tag.get_my_tags(0, 100, new_user, session)
    assert isinstance(tags, list)
    assert all(tag.user_id == new_user.id for tag in tags)

def test_get_all_tags_repo(session):
    tags = repository_tag.get_all_tags(0, 100, session)
    assert isinstance(tags, list)
    assert len(tags) >= 1

def test_get_tag_by_id_repo(tag, session):
    t = repository_tag.get_tag_by_id(tag.id, session)
    assert t.title == tag.title

def test_update_tag_repo(tag, session):
    body = HashtagBase(title="newtag")
    updated = repository_tag.update_tag(tag.id, body, session)
    assert updated.title == "newtag"

def test_remove_tag_repo(tag, session):
    repository_tag.remove_tag(tag.id, session)
    all_tags = repository_tag.get_all_tags(0, 100, session)
    assert all(t.id != tag.id for t in all_tags)

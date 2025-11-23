import pytest
from datetime import datetime
from app.database.models import User, Hashtag
from app.repository import hashtags as repository_tag
from app.schemas import HashtagBase

# ------------------- FIXTURES -------------------

@pytest.fixture()
def new_user(session):
    db_user = session.query(User).filter(User.email == "artur4ik@example.com").first()
    if not db_user:
        db_user = User(
            email="artur4ik@example.com",
            username="artur4ik",
            password="password123",
            is_verify=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


@pytest.fixture()
def tag(new_user, session):
    db_tag = session.query(Hashtag).first()
    if not db_tag:
        db_tag = Hashtag(
            title="dog",
            created_at=datetime.utcnow(),
            user_id=new_user.id
        )
        session.add(db_tag)
        session.commit()
        session.refresh(db_tag)
    return db_tag


@pytest.fixture()
def body():
    return {"title": "string"}


@pytest.fixture()
def new_body():
    return {"title": "dog"}


# ------------------- REPOSITORY TESTS -------------------

def test_create_tag_repo(body, new_user, session):
    tag_obj = HashtagBase(**body)
    response = repository_tag.create_tag(tag_obj, new_user, session)
    assert response.title == body["title"]
    assert response.user_id == new_user.id


def test_get_my_tags_repo(new_user, session):
    response = repository_tag.get_my_tags(0, 100, new_user, session)
    assert isinstance(response, list)
    assert all(tag.user_id == new_user.id for tag in response)


def test_get_all_tags_repo(session):
    response = repository_tag.get_all_tags(0, 100, session)
    assert isinstance(response, list)
    assert len(response) >= 1


def test_get_tag_by_id_repo(tag, session):
    response = repository_tag.get_tag_by_id(tag.id, session)
    assert response.title == tag.title


def test_update_tag_repo(tag, new_body, session):
    body_obj = HashtagBase(**new_body)
    response = repository_tag.update_tag(tag.id, body_obj, session)
    assert response.title == new_body["title"]


def test_remove_tag_repo(tag, session):
    repository_tag.remove_tag(tag.id, session)
    response = repository_tag.get_all_tags(0, 100, session)
    assert all(t.id != tag.id for t in response)


# ------------------- API TESTS -------------------

def test_create_tag(client, create_user):
    response = client.post("/api/hashtags/new/", json={"title": "dog"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "dog"


def test_get_all_tags(client, create_hashtags):
    response = client.get("/api/hashtags/all/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(create_hashtags)


def test_get_tag_by_id(client, create_hashtags):
    tag = create_hashtags[0]
    response = client.get(f"/api/hashtags/by_id/{tag.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tag.id


def test_update_tag(client, create_hashtags):
    tag = create_hashtags[0]
    response = client.put(f"/api/hashtags/upd_tag/{tag.id}", json={"title": "newtag"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "newtag"


def test_delete_tag(client, create_hashtags):
    tag = create_hashtags[0]
    response = client.delete(f"/api/hashtags/del/{tag.id}")
    assert response.status_code == 200

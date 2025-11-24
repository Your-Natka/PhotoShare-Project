import pytest
from app.database.models import User, Post, Comment
from app.services.auth import register_user

@pytest.fixture()
def new_user(db_session, faker):
    # генеруємо унікальний email для кожного тесту
    email = faker.unique.email()
    user = User(
        username="testuser",
        email=email,
        password="testpassword",
        is_verify=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture()
def post(new_user, db_session):
    post = Post(
        title="Test Post",
        content="Test content",
        owner_id=new_user.id
    )
    db_session.add(post)
    db_session.commit()
    return post

@pytest.fixture()
def comment(new_user, post, db_session):
    comment = Comment(
        content="Test comment",
        user_id=new_user.id,
        post_id=post.id
    )
    db_session.add(comment)
    db_session.commit()
    return comment

@pytest.mark.asyncio
async def test_create_comment(client, new_user, post):
    payload = {"content": "New comment", "post_id": post.id}
    response = await client.post("/api/comments/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "New comment"
    assert data["user_id"] == new_user.id
    assert data["post_id"] == post.id

@pytest.mark.asyncio
async def test_get_comments(client, post, comment):
    response = await client.get(f"/api/comments/?post_id={post.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["content"] == comment.content

@pytest.mark.asyncio
async def test_update_comment(client, comment):
    payload = {"content": "Updated comment"}
    response = await client.put(f"/api/comments/{comment.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated comment"

@pytest.mark.asyncio
async def test_delete_comment(client, comment):
    response = await client.delete(f"/api/comments/{comment.id}")
    assert response.status_code == 204



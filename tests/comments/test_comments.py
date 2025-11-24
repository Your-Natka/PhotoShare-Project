import pytest
import uuid
from app.database.models import User, Post, Comment

@pytest.fixture()
def new_user(db_session):
    # Генеруємо унікальний email для кожного тесту
    email = f"user_{uuid.uuid4().hex}@example.com"
    user = User(
        username="testuser",
        email=email,
        password="testpassword",
        is_verify=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    yield user
    db_session.delete(user)
    db_session.commit()

@pytest.fixture()
def post(new_user, db_session):
    post = Post(
        title="Test Post",
        body="Test content",
        owner_id=new_user.id
    )
    db_session.add(post)
    db_session.commit()
    yield post
    db_session.delete(post)
    db_session.commit()

@pytest.fixture()
def comment(new_user, post, db_session):
    comment = Comment(
        content="Test comment",
        user_id=new_user.id,
        post_id=post.id
    )
    db_session.add(comment)
    db_session.commit()
    yield comment
    db_session.delete(comment)
    db_session.commit()

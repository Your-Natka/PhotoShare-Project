import pytest
from datetime import datetime
from app.database.models import User, Comment, Post
from app.schemas import CommentBase
from app.repository import comments as repository_comments

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
def post(new_user, session):
    db_post = session.query(Post).first()
    if not db_post:
        db_post = Post(
            title="test_post",
            descr="test_post_descr",
            image_url="https://example.com/test.jpg",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            user_id=new_user.id,
            public_id="test_public",
            done=True
        )
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
    return db_post


@pytest.fixture()
def comment(new_user, post, session):
    db_comment = session.query(Comment).first()
    if not db_comment:
        db_comment = Comment(
            text="test_comment",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            user_id=new_user.id,
            post_id=post.id,
            update_status=False
        )
        session.add(db_comment)
        session.commit()
        session.refresh(db_comment)
    return db_comment

# ------------------- REPOSITORY TESTS -------------------

def test_create_comment_repo(post, new_user, session):
    comment_obj = CommentBase(text="test_comment_repo")
    response = repository_comments.create_comment(post.id, comment_obj, session, new_user)
    assert response.text == "test_comment_repo"
    assert response.user_id == new_user.id
    assert response.post_id == post.id


def test_edit_comment_repo(comment, session):
    new_comment_obj = CommentBase(text="edited_comment")
    response = repository_comments.edit_comment(comment.id, new_comment_obj, session, comment.user)
    assert response.text == "edited_comment"
    assert response.update_status is True


def test_delete_comment_repo(comment, session):
    response = repository_comments.delete_comment(comment.id, session, comment.user)
    assert response.id == comment.id


def test_show_single_comment_repo(comment, session):
    response = repository_comments.show_single_comment(comment.id, session, comment.user)
    assert response.text == comment.text


def test_show_user_comments_repo(new_user, session):
    response = repository_comments.show_user_comments(new_user.id, session)
    assert isinstance(response, list)
    if response:
        assert response[0].user_id == new_user.id


def test_show_user_post_comments_repo(new_user, post, session):
    response = repository_comments.show_user_post_comments(new_user.id, post.id, session)
    assert isinstance(response, list)
    if response:
        assert response[0].user_id == new_user.id


# ------------------- API TESTS -------------------

def test_create_comment(client, create_user, create_posts):
    post = create_posts[0]
    response = client.post(f"/api/comments/new/{post.id}", json={"text": "Test comment"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Test comment"


def test_get_comment_by_id(client, create_comments):
    comment = create_comments[0]
    response = client.get(f"/api/comments/single/{comment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == comment.id


def test_edit_comment(client, create_comments):
    comment = create_comments[0]
    response = client.put(f"/api/comments/edit/{comment.id}", json={"text": "Updated comment"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Updated comment"


def test_delete_comment(client, create_comments):
    comment = create_comments[0]
    response = client.delete(f"/api/comments/delete/{comment.id}")
    assert response.status_code == 200

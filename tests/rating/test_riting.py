import pytest
from datetime import datetime
from app.database.models import User, Post, Rating
from app.repository import ratings as repository_ratings

# ---------------- Fixtures ----------------
@pytest.fixture()
def new_user(session):
    email = "artur4ik@example.com"
    db_user = session.query(User).filter(User.email == email).first()
    if not db_user:
        db_user = User(
            email=email,
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
    db_post = session.query(Post).filter(Post.user_id == new_user.id).first()
    if not db_post:
        db_post = Post(
            image_url="https://example.com/image.jpg",
            title="cat",
            descr="pet",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            done=False,
            user_id=new_user.id,
            public_id="qwe"
        )
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
    return db_post

@pytest.fixture()
def rating(new_user, post, session):
    db_rating = session.query(Rating).filter(
        Rating.user_id == new_user.id,
        Rating.post_id == post.id
    ).first()
    if not db_rating:
        db_rating = Rating(
            rate=4,
            created_at=datetime.utcnow(),
            post_id=post.id,
            user_id=new_user.id
        )
        session.add(db_rating)
        session.commit()
        session.refresh(db_rating)
    return db_rating

# ---------------- Repository Tests ----------------
def test_create_rate(session, post, new_user):
    response = repository_ratings.create_rate(post.id, 5, session, new_user)
    assert response.rate == 5
    assert response.user_id == new_user.id
    assert response.post_id == post.id

def test_edit_rate(session, rating, new_user):
    response = repository_ratings.edit_rate(rating.id, 3, session, new_user)
    assert response.rate == 3
    assert response.user_id == new_user.id

def test_delete_rate(session, rating, new_user):
    response = repository_ratings.delete_rate(rating.id, session, new_user)
    assert response.rate == rating.rate
    assert response.user_id == new_user.id

def test_show_ratings(session, rating, new_user):
    response = repository_ratings.show_ratings(session, new_user)
    assert isinstance(response, list)
    assert response[0].rate == rating.rate

def test_show_my_ratings(session, new_user):
    response = repository_ratings.show_my_ratings(session, new_user)
    assert isinstance(response, list)

def test_user_rate_post(session, post, new_user):
    response = repository_ratings.user_rate_post(post.id, new_user.id, session, new_user)
    assert response.rate == 4
    assert response.user_id == new_user.id
    assert response.post_id == post.id

# ---------------- API Endpoint Tests ----------------
def test_create_rating_api(client, create_user, create_posts):
    post_obj = create_posts[0]
    response = client.post(f"/api/rating/new/{post_obj.id}", json={"value": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 5

def test_delete_rating_api(client, create_ratings):
    rating_obj = create_ratings[0]
    response = client.delete(f"/api/rating/{rating_obj.id}")
    assert response.status_code == 200

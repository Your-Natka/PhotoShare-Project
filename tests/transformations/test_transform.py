import io
from datetime import datetime
from unittest.mock import MagicMock
import pytest
from PIL import Image

from app.database.models import User, Post
from app.repository.transform_post import transform_metod, show_qr
from app.tramsform_schemas import TransformBodyModel

# -------------------- Fixtures --------------------
@pytest.fixture()
def new_user(db_session):
    email = "artur4ik@example.com"
    db_user = db_session.query(User).filter(User.email == email).first()
    if not db_user:
        db_user = User(
            email=email,
            username="artur4ik",
            password="password123",
            is_verify=True,
            is_active=True,
            role="admin"
        )
        db_session.add(db_user)
        db_session.commit()
        db_session.refresh(db_user)
    return db_user

@pytest.fixture()
def post(new_user, db_session):
    post_obj = db_session.query(Post).first()
    if not post_obj:
        post_obj = Post(
            image_url="https://res.cloudinary.com/dybgf2pue/image/upload/c_fill,h_250,w_250/Dominic",
            title="cat",
            descr="pet",
            created_at=datetime.now(),
            user_id=new_user.id,
            public_id="Dominic",
            done=True
        )
        db_session.add(post_obj)
        db_session.commit()
        db_session.refresh(post_obj)
    return post_obj

@pytest.fixture()
def post_id(post):
    return post.id

@pytest.fixture()
def body():
    return {
        "circle": {"use_filter": True, "height": 400, "width": 400},
        "effect": {"use_filter": True, "art_audrey": False, "art_zorro": True, "cartoonify": False, "blur": False},
        "resize": {"use_filter": True, "crop": True, "fill": False, "height": 400, "width": 400},
        "text": {"use_filter": True, "font_size": 70, "text": "Good"},
        "rotate": {"use_filter": False, "width": 400, "degree": 45}
    }

@pytest.fixture()
def token(client, new_user, db_session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("app.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/login", data={"username": new_user.email, "password": "password123"})
    return response.json()["access_token"]

# -------------------- Repository Async Tests --------------------
@pytest.mark.asyncio
async def test_transform_metod_repo(post, body, new_user, db_session):
    body_obj = TransformBodyModel(**body)
    response = await transform_metod(post.id, body_obj, new_user, db_session)
    assert post.image_url != response.transform_url

@pytest.mark.asyncio
async def test_show_qr_repo(post, new_user, db_session):
    response = await show_qr(post.id, new_user, db_session)
    assert isinstance(response, str)

# -------------------- API Endpoint Tests --------------------
def test_create_transformation_api(client, create_transformations):
    transform = create_transformations[0]
    response = client.get(f"/api/transformations/{transform.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transform.id

# -------------------- Minimal Additional Tests --------------------
def test_dummy_example(post):
    # Прості перевірки, щоб pytest точно запускав тести
    assert post.title == "cat"
    assert post.done is True

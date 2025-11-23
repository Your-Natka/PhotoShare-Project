import io
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image

from app.database.models import User, Post
from app.repository.transform_post import transform_metod, show_qr
from app.tramsform_schemas import TransformBodyModel
from app.services.auth import auth_service
from app.conf.messages import NOT_FOUND

# -------------------- Fixtures --------------------
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
            role="admin"
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


@pytest.fixture()
def post(new_user, session):
    post_obj = session.query(Post).first()
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
        session.add(post_obj)
        session.commit()
        session.refresh(post_obj)
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
def token(client, new_user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("app.routes.auth.send_email", mock_send_email)
    response = client.post("/api/auth/login", data={"username": new_user.email, "password": "password123"})
    return response.json()["access_token"]


# -------------------- Helper --------------------
def make_admin(session, email):
    user = session.query(User).filter(User.email == email).first()
    user.role = "admin"
    session.commit()
    return user


# -------------------- Repository Async Tests --------------------
@pytest.mark.asyncio
async def test_transform_metod_repo(post, body, new_user, session):
    body_obj = TransformBodyModel(**body)
    response = await transform_metod(post.id, body_obj, new_user, session)
    assert post.image_url != response.transform_url


@pytest.mark.asyncio
async def test_show_qr_repo(post, new_user, session):
    response = await show_qr(post.id, new_user, session)
    assert isinstance(response, str)


# -------------------- API Endpoint Tests --------------------
def test_create_transformation(client, create_transformations):
    transform = create_transformations[0]
    response = client.get(f"/api/transformations/{transform.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transform.id
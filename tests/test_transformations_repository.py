import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request

from app.repository.transform_post import transform_metod, show_qr
from app.database.models import Post, User
from app.tramsform_schemas import (
    TransformBodyModel,
    TransformCircleModel,
    TransformEffectModel,
    TransformResizeModel,
    TransformTextModel,
    TransformRotateModel   
)


# -----------------------------
# Fake DB session
# -----------------------------
class FakeDB:
    def __init__(self):
        self.posts = []
        self.committed = False

    def query(self, model):
        mock = MagicMock()
        mock.filter.return_value.first.side_effect = (
            lambda: self.posts[0] if self.posts else None
        )
        return mock

    def commit(self):
        self.committed = True


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def db():
    return FakeDB()

@pytest.fixture
def user():
    return User(id=1, username="john")

@pytest.fixture
def post():
    return Post(id=10, user_id=1, public_id="abc123", transform_url=None)

@pytest.fixture
def fake_request():
    scope = {
        "type": "http",
        "scheme": "http",
        "server": ("localhost", 8000),
        "headers": []
    }
    return Request(scope)


# -----------------------------
# TEST transform_metod
# -----------------------------
@pytest.mark.asyncio
@patch("app.repository.transform_post.cloudinary.CloudinaryImage")
@patch("app.repository.transform_post.init_cloudinary")
async def test_transform_method_full(
    mock_init_cloudinary, mock_cloud, db, user, post
):
    db.posts.append(post)

    # Мокуємо Cloudinary URL
    mock_instance = MagicMock()
    mock_instance.build_url.return_value = "http://cloud/test.jpg"
    mock_cloud.return_value = mock_instance

    # Тіло трансформації → всі фільтри активні
    body = TransformBodyModel(
        circle=TransformCircleModel(use_filter=True, height=200, width=200),
        effect=TransformEffectModel(use_filter=True, art_audrey=True),
        resize=TransformResizeModel(use_filter=True, height=300, width=300, crop=True),
        text=TransformTextModel(use_filter=True, font_size=20, text="Hello"),
        rotate=TransformRotateModel(use_filter=True, width=400, degree=90),
    )

    result = await transform_metod(post_id=10, body=body, user=user, db=db)

    assert result is not None
    assert result.transform_url == "http://cloud/test.jpg"
    mock_init_cloudinary.assert_called()


@pytest.mark.asyncio
async def test_transform_method_post_not_found(db, user):
    # Створюємо TransformBodyModel із дефолтними фільтрами
    body = TransformBodyModel(
        circle=TransformCircleModel(),
        effect=TransformEffectModel(),
        resize=TransformResizeModel(),
        text=TransformTextModel(),
        rotate=TransformRotateModel(),
    )
    result = await transform_metod(post_id=999, body=body, user=user, db=db)
    assert result is None


@pytest.mark.asyncio
@patch("app.repository.transform_post.cloudinary.CloudinaryImage")
async def test_transform_method_calls_cloudinary(mock_cloud, db, user, post):
    db.posts.append(post)

    body = TransformBodyModel(
        circle=TransformCircleModel(use_filter=True, height=100, width=100),
        effect=TransformEffectModel(),
        resize=TransformResizeModel(),
        text=TransformTextModel(),
        rotate=TransformRotateModel(),
    )

    mock_instance = MagicMock()
    mock_instance.build_url.return_value = "http://cloud/small.jpg"
    mock_cloud.return_value = mock_instance

    result = await transform_metod(10, body, user, db)

    mock_cloud.assert_called_with("abc123")
    assert result.transform_url == "http://cloud/small.jpg"
    assert db.committed is True


# -----------------------------
# TEST show_qr
# -----------------------------
@pytest.mark.asyncio
@patch("app.repository.transform_post.pyqrcode.create")
async def test_show_qr_success(mock_qr, tmp_path, db, post, user, fake_request, monkeypatch):
    # Гарантуємо media/qrcodes → у тимчасову папку
    qr_dir = tmp_path / "media" / "qrcodes"
    monkeypatch.setattr("app.repository.transform_post.os.makedirs", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.repository.transform_post.os.path", MagicMock())

    db.posts.append(post)
    post.transform_url = "http://cloud/result.jpg"

    mock_png = MagicMock()
    mock_qr.return_value = mock_png

    result = await show_qr(10, user, db, fake_request)

    assert "qr_url" in result
    assert result["qr_url"].endswith("10.png")
    mock_png.png.assert_called()


@pytest.mark.asyncio
async def test_show_qr_no_post(db, user, fake_request):
    result = await show_qr(10, user, db, fake_request)
    assert result is None


@pytest.mark.asyncio
async def test_show_qr_no_transform_url(db, user, post, fake_request):
    db.posts.append(post)
    post.transform_url = None

    result = await show_qr(10, user, db, fake_request)
    assert result is None

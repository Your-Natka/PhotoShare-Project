import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repository import transform_post
from app.tramsform_schemas import (
    TransformBodyModel,
    TransformCircleModel,
    TransformEffectModel,
    TransformResizeModel,
    TransformTextModel,
    TransformRotateModel
)
from app.database.models import Post, User

@pytest.mark.asyncio
async def test_transform_metod_applies_transformation(mocker):
    # Мок користувача і поста
    user = User(id=1)
    post = Post(id=1, user_id=1, public_id="test_public_id", transform_url=None)

    # Мок бази даних
    db = MagicMock()
    db.query().filter().first.return_value = post
    db.commit = MagicMock()

    # Мок CloudinaryImage.build_url
    mock_build_url = mocker.patch("cloudinary.CloudinaryImage.build_url", return_value="http://cloudinary/test.jpg")

    # Тіло трансформацій
    body = TransformBodyModel(
        circle=TransformCircleModel(use_filter=True),
        effect=TransformEffectModel(use_filter=True, art_audrey=True),
        resize=TransformResizeModel(use_filter=True, crop=True),
        text=TransformTextModel(use_filter=True, text="Hello"),
        rotate=TransformRotateModel(use_filter=True)
    )

    transformed_post = await transform_post.transform_metod(post_id=1, body=body, user=user, db=db)

    assert transformed_post.transform_url == "http://cloudinary/test.jpg"
    db.commit.assert_called_once()
    mock_build_url.assert_called_once()


@pytest.mark.asyncio
async def test_show_qr_returns_url(tmp_path, mocker):
    user = User(id=1)
    post = Post(id=1, user_id=1, transform_url="http://cloudinary/test.jpg")
    db = MagicMock()
    db.query().filter().first.return_value = post

    # Мок request.base_url
    request = MagicMock()
    request.base_url = "http://testserver/"

    # Мок pyqrcode.create
    mock_img = mocker.patch("pyqrcode.create")
    mock_png = MagicMock()
    mock_img.return_value.png = mock_png

    result = await transform_post.show_qr(post_id=1, user=user, db=db, request=request)
    assert "qr_url" in result
    mock_png.assert_called_once()

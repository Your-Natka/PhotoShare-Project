"""
transform.py — функції для обробки трансформацій постів та генерації QR-кодів.

Містить:
- transform_metod: застосування ефектів, кадрування, тексту та обертання через Cloudinary
- show_qr: генерація QR-коду для трансформованого поста
"""

import os
from fastapi import Request
from sqlalchemy.orm import Session
import cloudinary
import pyqrcode

from app.database.models import Post, User
from app.conf.config import init_cloudinary
from app.tramsform_schemas import TransformBodyModel
from app.conf.messages import NOT_FOUND


def transform_metod(post_id: int, body: TransformBodyModel, user: User, db: Session) -> Post | None:
    post = db.query(Post).filter(Post.user_id == user.id, Post.id == post_id).first()
    if post:
        transformation = []

        # Круглий кадр
        if body.circle.use_filter and body.circle.height and body.circle.width:
            trans_list = [
                {'gravity': "face", 'height': f"{body.circle.height}", 'width': f"{body.circle.width}", 'crop': "thumb"},
                {'radius': "max"}
            ]
            [transformation.append(elem) for elem in trans_list]

        # Ефекти
        if body.effect.use_filter:
            effect = ""
            if body.effect.art_audrey:
                effect = "art:audrey"
            if body.effect.art_zorro:
                effect = "art:zorro"
            if body.effect.blur:
                effect = "blur:300"
            if body.effect.cartoonify:
                effect = "cartoonify"
            if effect:
                transformation.append({"effect": f"{effect}"})

        # Resize
        if body.resize.use_filter and body.resize.height and body.resize.width:
            crop = "crop" if body.resize.crop else "fill" if body.resize.fill else ""
            if crop:
                trans_list = [{"gravity": "auto", 'height': f"{body.resize.height}", 'width': f"{body.resize.width}", 'crop': f"{crop}"}]
                [transformation.append(elem) for elem in trans_list]

        # Текст
        if body.text.use_filter and body.text.font_size and body.text.text:
            trans_list = [
                {'color': "#FFFF00", 'overlay': {'font_family': "Times", 'font_size': f"{body.text.font_size}", 'font_weight': "bold", 'text': f"{body.text.text}"}},
                {'flags': "layer_apply", 'gravity': "south", 'y': 20}
            ]
            [transformation.append(elem) for elem in trans_list]

        # Обертання
        if body.rotate.use_filter and body.rotate.width and body.rotate.degree:
            trans_list = [{'width': f"{body.rotate.width}", 'crop': "scale"}, {'angle': "vflip"}, {'angle': f"{body.rotate.degree}"}]
            [transformation.append(elem) for elem in trans_list]

        if transformation:
            init_cloudinary()
            url = cloudinary.CloudinaryImage(post.public_id).build_url(
                transformation=transformation
            )
            post.transform_url = url
            db.commit()

        return post
    return None


def show_qr(post_id: int, user: User, db: Session, request: Request) -> dict | None:
    post = db.query(Post).filter(Post.user_id == user.id, Post.id == post_id).first()
    if post and post.transform_url:
        qr_dir = "media/qrcodes"
        os.makedirs(qr_dir, exist_ok=True)

        img = pyqrcode.create(post.transform_url)
        qr_path = f"{qr_dir}/{post.id}.png"
        img.png(qr_path, scale=6)

        base_url = str(request.base_url).rstrip("/")
        qr_url = f"{base_url}/{qr_path}"
        return {"qr_url": qr_url}

    return None

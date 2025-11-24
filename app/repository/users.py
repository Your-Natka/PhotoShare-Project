"""
users.py — функції для роботи з користувачами та чорним списком токенів.

Містить:
- CRUD для користувачів
- Управління аватарками через Cloudinary
- Робота з ролями, блокуванням та підтвердженням email
- Робота з чорним списком JWT токенів
"""

from datetime import datetime
from typing import List, Optional

import cloudinary
import cloudinary.uploader
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.conf.config import init_cloudinary
from app.database.models import User, UserRoleEnum, Comment, Rating, Post, BlacklistToken
from app.schemas import UserModel, UserProfileModel


# ---------------- USER CRUD ---------------- #

def get_me(user: User, db: Session) -> User:
    return db.query(User).filter(User.id == user.id).first()


def edit_my_profile(file, new_username: Optional[str], user: User, db: Session) -> User:
    me = db.query(User).filter(User.id == user.id).first()
    if new_username:
        me.username = new_username

    if file:
        init_cloudinary()
        cloudinary.uploader.upload(
            file.file,
            public_id=f'Photoshare/{me.username}',
            overwrite=True,
            invalidate=True
        )
        url = cloudinary.CloudinaryImage(f'Photoshare/{me.username}').build_url(width=250, height=250, crop='fill')
        me.avatar = url

    db.commit()
    db.refresh(me)
    return me


def get_users(skip: int, limit: int, db: Session) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def get_users_with_username(username: str, db: Session) -> List[User]:
    return db.query(User).filter(func.lower(User.username).like(f'%{username.lower()}%')).all()


def get_user_profile(username: str, db: Session) -> Optional[UserProfileModel]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None

    post_count = db.query(Post).filter(Post.user_id == user.id).count()
    comment_count = db.query(Comment).filter(Comment.user_id == user.id).count()
    rates_count = db.query(Rating).filter(Rating.user_id == user.id).count()

    return UserProfileModel(
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        created_at=user.created_at,
        is_active=user.is_active,
        post_count=post_count,
        comment_count=comment_count,
        rates_count=rates_count
    )


def get_all_commented_posts(user: User, db: Session) -> List[Post]:
    return db.query(Post).join(Comment).filter(Comment.user_id == user.id).all()


def get_all_liked_posts(user: User, db: Session) -> List[Post]:
    return db.query(Post).join(Rating).filter(Rating.user_id == user.id).all()


def get_user_by_email(email: str, db: Session) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(body: UserModel, db: Session) -> User:
    new_user = User(**body.dict())
    if db.query(User).count() == 0:
        new_user.role = UserRoleEnum.admin
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_token(user: User, token: Optional[str], db: Session) -> None:
    user.refresh_token = token
    db.commit()


def confirmed_email(email: str, db: Session) -> None:
    user = get_user_by_email(email, db)
    if user:
        user.is_verify = True
        db.commit()


def ban_user(email: str, db: Session) -> None:
    user = get_user_by_email(email, db)
    if user:
        user.is_active = False
        db.commit()


def make_user_role(email: str, role: UserRoleEnum, db: Session) -> None:
    user = get_user_by_email(email, db)
    if user:
        user.role = role
        db.commit()


# ---------------- BLACKLIST ---------------- #

def add_to_blacklist(token: str, db: Session) -> None:
    if not find_blacklisted_token(token, db):
        blacklist_token = BlacklistToken(token=token, blacklisted_on=datetime.utcnow())
        db.add(blacklist_token)
        db.commit()


def find_blacklisted_token(token: str, db: Session) -> Optional[BlacklistToken]:
    return db.query(BlacklistToken).filter(BlacklistToken.token == token).first()


def remove_from_blacklist(token: str, db: Session) -> None:
    blacklist_token = find_blacklisted_token(token, db)
    if blacklist_token:
        db.delete(blacklist_token)
        db.commit()

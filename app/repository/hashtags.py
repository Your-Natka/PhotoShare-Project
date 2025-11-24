"""
hashtags.py — функції для роботи з хештегами у PhotoShare API.

Містить CRUD-операції та методи для отримання тегів користувачів і загальних тегів.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Hashtag, User
from app.schemas import HashtagBase


def create_tag(body: HashtagBase, user: User, db: Session) -> Hashtag:
    """
    Створює новий хештег або повертає існуючий, якщо він вже є.
    """
    tag = db.query(Hashtag).filter(Hashtag.title == body.title).first()
    if not tag:
        tag = Hashtag(
            title=body.title,
            user_id=user.id,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
    return tag


def get_my_tags(skip: int, limit: int, user: User, db: Session) -> List[Hashtag]:
    """
    Повертає список хештегів, створених поточним користувачем.
    """
    return (
        db.query(Hashtag)
        .filter(Hashtag.user_id == user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_tags(skip: int, limit: int, db: Session) -> List[Hashtag]:
    """
    Повертає список усіх тегів у системі.
    """
    return db.query(Hashtag).offset(skip).limit(limit).all()


def get_tag_by_id(tag_id: int, db: Session) -> Optional[Hashtag]:
    """
    Повертає конкретний хештег за його ID.
    """
    return db.query(Hashtag).filter(Hashtag.id == tag_id).first()


def update_tag(tag_id: int, body: HashtagBase, db: Session) -> Optional[Hashtag]:
    """
    Оновлює назву хештегу за його ID.
    """
    tag = db.query(Hashtag).filter(Hashtag.id == tag_id).first()
    if tag:
        tag.title = body.title
        db.commit()
        db.refresh(tag)
    return tag


def remove_tag(tag_id: int, db: Session) -> Optional[Hashtag]:
    """
    Видаляє хештег за його ID.
    """
    tag = db.query(Hashtag).filter(Hashtag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
    return tag

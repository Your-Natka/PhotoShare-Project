"""
comments.py — функції для роботи з коментарями у PhotoShare API.

Містить CRUD-операції та методи для отримання коментарів користувачів.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException
from app.database.models import User, Comment, UserRoleEnum
from app.schemas import CommentBase


def create_comment(post_id: int, body: CommentBase, db: Session, user: User) -> Comment:
    """
    Створює новий коментар для конкретного посту.
    """
    new_comment = Comment(
        text=body.text,
        post_id=post_id,
        user_id=user.id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


def edit_comment(comment_id: int, body: CommentBase, db: Session, user: User) -> Comment:
    """
    Редагує існуючий коментар.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or not available.")
    
    if comment.user_id != user.id and user.role not in [UserRoleEnum.admin, UserRoleEnum.moder]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment.")

    comment.text = body.text
    comment.updated_at = func.now()
    comment.update_status = True

    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(comment_id: int, db: Session, user: User) -> Optional[Comment]:
    """
    Видаляє коментар.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment and (user.role in [UserRoleEnum.admin, UserRoleEnum.moder] or comment.user_id == user.id):
        db.delete(comment)
        db.commit()
        return comment
    return None


def show_single_comment(comment_id: int, db: Session, user: User) -> Optional[Comment]:
    """
    Повертає конкретний коментар.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment and (comment.user_id == user.id or user.role in [UserRoleEnum.admin, UserRoleEnum.moder]):
        return comment
    return None


def show_user_comments(user_id: int, db: Session) -> List[Comment]:
    """
    Повертає список всіх коментарів користувача.
    """
    return db.query(Comment).filter(Comment.user_id == user_id).all()


def show_user_post_comments(user_id: int, post_id: int, db: Session) -> List[Comment]:
    """
    Повертає список коментарів користувача під конкретним постом.
    """
    return db.query(Comment).filter(
        and_(Comment.post_id == post_id, Comment.user_id == user_id)
    ).all()

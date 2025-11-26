"""
posts.py — функції для роботи з постами у PhotoShare API.

Містить CRUD-операції над постами, пошук за ключовими словами та хештегами, а також роботу з Cloudinary.
"""

from typing import List
from datetime import datetime
from fastapi import Request, UploadFile
from faker import Faker
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader

from app.conf.config import init_cloudinary
from app.database.models import Post, Hashtag, User, Comment, UserRoleEnum
from app.schemas import PostUpdate

# Ініціалізація Cloudinary один раз
init_cloudinary()

async def get_posts(skip: int = 0, limit: int = 100, db: Session = None):
    return await get_all_posts(skip=skip, limit=limit, db=db)

async def create_post(
    request: Request,
    title: str,
    descr: str,
    hashtags: List[str],
    file: UploadFile,
    db: Session,
    current_user: User
) -> Post:
    """
    Створює новий пост з завантаженим зображенням у Cloudinary та додає хештеги.

    :param request: FastAPI Request об'єкт
    :param title: Заголовок поста
    :param descr: Опис поста
    :param hashtags: Список хештегів
    :param file: Файл зображення
    :param db: SQLAlchemy сесія
    :param current_user: Поточний користувач
    :return: Створений об'єкт Post
    """
    public_id = Faker().first_name()
    upload_result = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    url = upload_result.get("secure_url")

    tag_objs = []
    if hashtags:
        tag_objs = get_hashtags([tag.strip() for tag in hashtags[0].split(",")], current_user, db)

    post = Post(
        image_url=url,
        title=title,
        descr=descr,
        created_at=datetime.now(),
        user_id=current_user.id,
        hashtags=tag_objs,
        public_id=public_id,
        done=True
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


async def get_all_posts(skip: int, limit: int, db: Session) -> List[Post]:
    """
    Повертає всі пости з пагінацією.

    :param skip: Кількість пропущених постів
    :param limit: Ліміт постів для повернення
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    return db.query(Post).offset(skip).limit(limit).all()


async def get_my_posts(skip: int, limit: int, user: User, db: Session) -> List[Post]:
    """
    Повертає всі пости поточного користувача.

    :param skip: Кількість пропущених постів
    :param limit: Ліміт постів для повернення
    :param user: Поточний користувач
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    return db.query(Post).filter(Post.user_id == user.id).offset(skip).limit(limit).all()


async def get_post_by_id(post_id: int, user: User, db: Session) -> Post | None:
    """
    Повертає конкретний пост поточного користувача за ID.

    :param post_id: ID поста
    :param user: Поточний користувач
    :param db: SQLAlchemy сесія
    :return: Об'єкт Post або None, якщо пост не знайдено
    """
    return db.query(Post).filter(and_(Post.user_id == user.id, Post.id == post_id)).first()


async def get_posts_by_title(post_title: str, user: User, db: Session) -> List[Post]:
    """
    Повертає пости, які містять заданий заголовок.

    :param post_title: Заголовок для пошуку
    :param user: Поточний користувач
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    return db.query(Post).filter(func.lower(Post.title).like(f'%{post_title.lower()}%')).all()


async def get_posts_by_user_id(user_id: int, db: Session) -> List[Post]:
    """
    Повертає всі пости певного користувача за його ID.

    :param user_id: ID користувача
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    return db.query(Post).filter(Post.user_id == user_id).all()


async def get_posts_by_username(user_name: str, db: Session) -> List[Post]: 
    """
    Повертає всі пости користувача за його username.

    :param user_name: Username користувача
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    searched_user = db.query(User).filter(func.lower(User.username).like(f'%{user_name.lower()}%')).first()
    if searched_user:
        return db.query(Post).filter(Post.user_id == searched_user.id).all()
    return []


async def get_posts_with_hashtag(hashtag_name: str, db: Session) -> List[Post]: 
    """
    Повертає пости, які містять конкретний хештег.

    :param hashtag_name: Назва хештегу
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    return db.query(Post).join(Post.hashtags).filter(Hashtag.title == hashtag_name).all()


async def get_post_comments(post_id: int, db: Session) -> List[Comment]: 
    """
    Повертає коментарі для конкретного поста.

    :param post_id: ID поста
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Comment
    """
    return db.query(Comment).filter(Comment.post_id == post_id).all()


def get_hashtags(hashtag_titles: list, user: User, db: Session):
    """
    Створює або отримує існуючі хештеги за списком назв.

    :param hashtag_titles: Список назв хештегів
    :param user: Поточний користувач
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Hashtag
    """
    tags = []
    for tag_title in hashtag_titles:
        tag = db.query(Hashtag).filter(Hashtag.title == tag_title).first()
        if not tag:
            tag = Hashtag(title=tag_title, user_id=user.id)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        tags.append(tag)
    return tags


async def get_post_by_keyword(keyword: str, db: Session) -> List[Post]:
    """
    Повертає пости, які містять ключове слово в заголовку або описі.

    :param keyword: Ключове слово для пошуку
    :param db: SQLAlchemy сесія
    :return: Список об'єктів Post
    """
    return db.query(Post).filter(or_(
        func.lower(Post.title).like(f'%{keyword.lower()}%'),
        func.lower(Post.descr).like(f'%{keyword.lower()}%')
    )).all()


async def update_post(post_id: int, body: PostUpdate, user: User, db: Session) -> Post | None:
    """
    Оновлює пост користувача або адміністраторський пост.

    :param post_id: ID поста
    :param body: Дані для оновлення (PostUpdate)
    :param user: Поточний користувач
    :param db: SQLAlchemy сесія
    :return: Оновлений об'єкт Post або None
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if post and (user.role == UserRoleEnum.admin or post.user_id == user.id):
        # оновлюємо хештеги лише якщо вони присутні
        if body.hashtags is not None:
            post.hashtags = get_hashtags(body.hashtags, user, db)

        # оновлюємо інші поля, якщо вони присутні
        if body.title is not None:
            post.title = body.title
        if body.descr is not None:
            post.descr = body.descr

        post.updated_at = datetime.now()
        post.done = True
        db.commit()
        db.refresh(post)
    return post
    # post = db.query(Post).filter(Post.id == post_id).first()
    # if post and (user.role == UserRoleEnum.admin or post.user_id == user.id):
    #     hashtags = []
    #     if body.hashtags:
    #         hashtags = get_hashtags(body.hashtags, user, db)
    #     post.title = body.title
    #     post.descr = body.descr
    #     post.hashtags = hashtags
    #     post.updated_at = datetime.now()
    #     post.done = True
    #     db.commit()
    # return post


async def remove_post(post_id: int, user: User, db: Session) -> Post | None:
    """
    Видаляє пост користувача або адміністраторський пост та його файл з Cloudinary.

    :param post_id: ID поста
    :param user: Поточний користувач
    :param db: SQLAlchemy сесія
    :return: Видалений об'єкт Post або None
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if post and (user.role == UserRoleEnum.admin or post.user_id == user.id):
        cloudinary.uploader.destroy(post.public_id)
        db.delete(post)
        db.commit()
    return post

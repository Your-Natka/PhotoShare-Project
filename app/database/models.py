"""
models.py — моделі бази даних для PhotoShare API.

Містить:
- Користувачів (User) з ролями
- Пост (Post) та пов'язані таблиці
- Хештеги (Hashtag) з Many-to-Many до постів
- Коментарі (Comment)
- Рейтинги (Rating)
- Чорний список токенів (BlacklistToken)
"""

import enum
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, func, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy_utils import aggregated

Base = declarative_base()

# ---------------- ENUMS ---------------- #
class UserRoleEnum(enum.Enum):
    """Ролі користувачів у системі"""
    user = 'User'
    moder = 'Moderator'
    admin = 'Administrator'


# ---------------- USER ---------------- #
class User(Base):
    """
    Користувачі системи.
    Перший користувач завжди адміністратор.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=True)
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    avatar = Column(String(355), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.user)
    refresh_token = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verify = Column(Boolean, default=False)

    posts = relationship('Post', back_populates='user', cascade="all, delete-orphan")
    comments = relationship('Comment', back_populates='user', cascade="all, delete-orphan")
    ratings = relationship('Rating', back_populates='user', cascade="all, delete-orphan")
    hashtags = relationship('Hashtag', back_populates='user', cascade="all, delete-orphan")


# ---------------- MANY-TO-MANY POSTS-HASHTAGS ---------------- #
post_m2m_hashtag = Table(
    "post_m2m_hashtag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE")),
    Column("hashtag_id", Integer, ForeignKey("hashtags.id", ondelete="CASCADE")),
)


# ---------------- POST ---------------- #
class Post(Base):
    """
    Пост зі світлиною, описом та трансформаціями.
    Підтримує хештеги, рейтинги та коментарі.
    """
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    image_url = Column(String(300))
    transform_url = Column(Text)
    title = Column(String(50), nullable=True)
    descr = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    done = Column(Boolean, default=False)
    public_id = Column(String(50))

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    user = relationship('User', back_populates='posts')

    hashtags = relationship('Hashtag', secondary=post_m2m_hashtag, back_populates='posts')
    rating = relationship('Rating', back_populates='post', cascade="all, delete-orphan")
    comments = relationship('Comment', back_populates='post', cascade="all, delete-orphan")

    @aggregated('rating', Column(Numeric))
    def avg_rating(self):
        """Середній рейтинг посту"""
        return func.avg(Rating.rate)


# ---------------- HASHTAG ---------------- #
class Hashtag(Base):
    """Унікальний тег для постів."""
    __tablename__ = 'hashtags'

    id = Column(Integer, primary_key=True)
    title = Column(String(25), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    user = relationship('User', back_populates='hashtags')
    posts = relationship('Post', secondary=post_m2m_hashtag, back_populates='hashtags')


# ---------------- COMMENT ---------------- #
class Comment(Base):
    """
    Коментар до посту.
    Користувач може редагувати, адмін/модератор — видаляти.
    """
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=None)
    update_status = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=True)

    user = relationship('User', back_populates='comments')
    post = relationship('Post', back_populates='comments')


# ---------------- RATING ---------------- #
class Rating(Base):
    """Рейтинг посту від користувачів від 1 до 5 зірок."""
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True)
    rate = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    user = relationship('User', back_populates='ratings')
    post = relationship('Post', back_populates='rating')


# ---------------- BLACKLIST ---------------- #
class BlacklistToken(Base):
    """Чорний список токенів для logout."""
    __tablename__ = 'blacklist_tokens'

    id = Column(Integer, primary_key=True)
    token = Column(String(500), unique=True, nullable=False)
    blacklisted_on = Column(DateTime, default=func.now())

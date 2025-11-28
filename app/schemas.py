from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.database.models import UserRoleEnum

# ------------------- User Models -------------------

class UserModel(BaseModel):
    """
    Модель для створення користувача.
    """
    username: str = Field(min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(min_length=6, max_length=30)
    avatar: Optional[str] = None
    created_at: Optional[datetime] = None


class UserUpdateModel(BaseModel):
    """
    Модель для оновлення username користувача.
    """
    username: str = Field(min_length=5, max_length=25)


class UserDb(BaseModel):
    """
    Модель користувача для відповіді із бази даних.
    """
    id: int
    username: str
    email: str
    avatar: Optional[str]
    role: UserRoleEnum
    created_at: Optional[datetime]

    # model_config = {"from_attributes": True}
    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    """
    Відповідь при створенні користувача.
    """
    user: UserDb
    detail: str = "User successfully created"


class UserProfileModel(BaseModel):
    """
    Повний профіль користувача.
    """
    username: str
    email: EmailStr
    avatar: Optional[str]
    post_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    rates_count: Optional[int] = 0
    is_active: Optional[bool] = True
    created_at: datetime


# ------------------- Auth / Token -------------------

class TokenModel(BaseModel):
    """
    Модель токенів для аутентифікації.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ------------------- Hashtags -------------------

class HashtagBase(BaseModel):
    title: str = Field(max_length=50)


class HashtagModel(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HashtagResponse(HashtagModel):
    """
    Відповідь з інформацією про хештег.
    """
    id: int
    title: str   # <-- замість name
    user_id: int
    
    model_config = {"from_attributes": True}


class HashtagsLimited(BaseModel):
    """
    Модель для обмеження кількості хештегів до 5.
    """
    hashtags: List[str] = Field(default_factory=list)

    @field_validator("hashtags")
    def validate_tags(cls, v):
        if len(v or []) > 5:
            raise ValueError("Too many hashtags. Maximum 5 tags allowed.")
        return v


# ------------------- Comments -------------------

class CommentBase(BaseModel):
    text: str = Field(max_length=500)


class CommentResponse(CommentBase):
    id: int
    text: str
    user_id: int
    post_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CommentUpdate(BaseModel):
    """
    Модель для оновлення коментаря.
    """
    text: str = Field(max_length=500)

    model_config = {"from_attributes": True}


# ------------------- Ratings -------------------

class RatingBase(BaseModel):
    rate: int = Field(ge=1, le=5)


class RatingModel(RatingBase):
    id: int
    created_at: datetime
    post_id: int
    user_id: int

    model_config = {"from_attributes": True}


# ------------------- Posts -------------------

class PostBase(BaseModel):
    """
    Базова модель поста.
    """
    image_url: Optional[str] = Field(max_length=300, default=None)
    transform_url: Optional[str] = Field(max_length=450, default=None)
    title: str = Field(max_length=45)
    descr: str = Field(max_length=450)


class PostModel(PostBase, HashtagsLimited):
    """
    Модель поста із хештегами.
    """
    pass


class PostUpdate(PostBase):
    """
    Модель для оновлення поста.
    """
    title: str = Field(max_length=45)
    descr: str = Field(max_length=450)
    hashtags: Optional[List[str]] = None


class PostResponse(PostBase):
    """
    Відповідь при отриманні поста.
    """
    id: int
    hashtags: List[HashtagModel]
    avg_rating: Optional[float] = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ------------------- Email / Roles -------------------

class RequestEmail(BaseModel):
    email: EmailStr


class RequestRole(BaseModel):
    email: EmailStr
    role: UserRoleEnum

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, Request
from typing import List
from sqlalchemy.orm import Session
from app.database.connect_db import get_db
from app.database.models import User, UserRoleEnum
from app.schemas import CommentResponse, PostResponse, PostUpdate
from app.repository import posts as repository_posts
from app.services.auth import auth_service
from app.services.roles import RoleChecker
from app.conf.messages import NOT_FOUND

router = APIRouter(prefix='/posts', tags=["posts"])

# Ролі для доступу
allowed_get_all_posts = RoleChecker([UserRoleEnum.admin])

# --- допоміжна функція для обробки хештегів ---
def serialize_hashtags(post):
    """
    Перетворює об'єкти хештегів у список рядків.
    """
    post.hashtags = [h.name if hasattr(h, 'name') else h for h in post.hashtags]
    return post

# --------------------------------------------
# CREATE POST
# --------------------------------------------
@router.post("/new/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_new_post(
    request: Request,
    title: str,
    descr: str,
    hashtags: List[str],
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Створює новий пост користувача.
    
    - **title**: Заголовок поста
    - **descr**: Опис поста
    - **hashtags**: Список хештегів (максимум 5)
    - **file**: Файл для поста
    """
    if len(hashtags) > 5:
        raise HTTPException(status_code=400, detail="You can only add up to 5 hashtags per post")

    post = await repository_posts.create_post(request, title, descr, hashtags, file, db, current_user)
    return serialize_hashtags(post)

# --------------------------------------------
# READ POSTS
# --------------------------------------------
@router.get("/my_posts", response_model=List[PostResponse])
async def read_all_user_posts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Повертає всі пости поточного користувача (з пагінацією).
    """
    posts = await repository_posts.get_my_posts(skip, limit, current_user, db)
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

    result = [serialize_hashtags(PostResponse.from_orm(post)) for post in posts]
    return result

@router.get("/all", response_model=List[PostResponse], dependencies=[Depends(allowed_get_all_posts)])
async def read_all_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Повертає всі пости (для адміністратора) з пагінацією.
    """
    posts = await repository_posts.get_all_posts(skip, limit, db)
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return [serialize_hashtags(post) for post in posts]

@router.get("/by_id/{post_id}", response_model=PostResponse)
async def read_post_by_id(post_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає пост за його ID.
    """
    post = await repository_posts.get_post_by_id(post_id, current_user, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return serialize_hashtags(post)

@router.get("/by_title/{post_title}", response_model=List[PostResponse])
async def read_posts_with_title(post_title: str, db: Session = Depends(get_db),
                                current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає список постів за назвою.
    """
    posts = await repository_posts.get_posts_by_title(post_title, current_user, db)
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return [serialize_hashtags(post) for post in posts]

@router.get("/by_user_id/{user_id}", response_model=List[PostResponse])
async def read_posts_by_user_id(user_id: int, db: Session = Depends(get_db),
                                current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає пости користувача за ID.
    """
    posts = await repository_posts.get_posts_by_user_id(user_id, db) or []
    return [serialize_hashtags(PostResponse.from_orm(post)) for post in posts]

@router.get("/by_username/{user_name}", response_model=List[PostResponse])
async def read_post_with_user_username(user_name: str, db: Session = Depends(get_db),
                                       current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає пости користувача за username.
    """
    posts = await repository_posts.get_posts_by_username(user_name, db)
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return [serialize_hashtags(post) for post in posts]

@router.get("/with_hashtag/{hashtag_name}", response_model=List[PostResponse])
async def read_post_with_hashtag(hashtag_name: str, db: Session = Depends(get_db),
                                 current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає список постів з певним хештегом.
    """
    posts = await repository_posts.get_posts_with_hashtag(hashtag_name, db)
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return [serialize_hashtags(post) for post in posts]

@router.get("/by_keyword/{keyword}", response_model=List[PostResponse])
async def read_posts_by_keyword(keyword: str, db: Session = Depends(get_db),
                                current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає пости, де в заголовку або описі є ключове слово.
    """
    posts = await repository_posts.get_post_by_keyword(keyword, db)
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return [serialize_hashtags(post) for post in posts]

# --------------------------------------------
# COMMENTS
# --------------------------------------------
@router.get("/comments/all/{post_id}", response_model=List[CommentResponse])
async def read_post_comments(post_id: int, db: Session = Depends(get_db),
                             current_user: User = Depends(auth_service.get_current_user)):
    """
    Повертає список коментарів для поста.
    """
    comments = await repository_posts.get_post_comments(post_id, db)
    if not comments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return comments

# --------------------------------------------
# UPDATE POST
# --------------------------------------------
@router.put("/{post_id}", response_model=PostResponse)
async def update_post(body: PostUpdate, post_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    """
    Оновлює пост за його ID.
    """
    post = await repository_posts.update_post(post_id, body, current_user, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return serialize_hashtags(post)

# --------------------------------------------
# DELETE POST
# --------------------------------------------
@router.delete("/{post_id}", response_model=PostResponse)
async def remove_post(post_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    """
    Видаляє пост за його ID.
    """
    post = await repository_posts.remove_post(post_id, current_user, db)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return serialize_hashtags(post)

async def rate_limiter(*args, **kwargs):
    return True
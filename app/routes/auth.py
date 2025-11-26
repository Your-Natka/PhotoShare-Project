from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.models import User
from app.services.email import send_email
from app.database.connect_db import get_db
from app.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from app.repository import users as repository_users
from app.services.auth import auth_service
from app.conf.messages import (
    ALREADY_EXISTS, EMAIL_ALREADY_CONFIRMED, EMAIL_CONFIRMED,
    EMAIL_NOT_CONFIRMED, INVALID_EMAIL, INVALID_PASSWORD, INVALID_TOKEN,
    SUCCESS_CREATE_USER, VERIFICATION_ERROR,
    CHECK_YOUR_EMAIL, USER_NOT_ACTIVE, USER_IS_LOGOUT
)

router = APIRouter(prefix='/auth', tags=["authentication"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Реєстрація нового користувача.
    - Перевіряє, чи користувач вже існує.
    - Хешує пароль.
    - Створює користувача.
    - Відправляє email для підтвердження.

    :param body: Дані нового користувача
    :param background_tasks: Використовується для асинхронної відправки email
    :param request: FastAPI Request для побудови URL
    :param db: SQLAlchemy сесія
    :return: UserResponse з повідомленням
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ALREADY_EXISTS)

    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created"}


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Авторизація користувача.
    - Перевіряє email і пароль.
    - Перевіряє підтвердження email.
    - Перевіряє активність користувача.
    - Генерує access та refresh токени.

    :param body: OAuth2PasswordRequestForm з username та password
    :param db: SQLAlchemy сесія
    :return: TokenModel з access та refresh токенами
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_EMAIL)
    if not user.is_verify:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=EMAIL_NOT_CONFIRMED)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=USER_NOT_ACTIVE)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_PASSWORD)

    access_token = await auth_service.create_access_token(data={"sub": user.email}, expires_delta=7200)
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Вихід користувача.
    - Додає access токен у чорний список.

    :param credentials: HTTPAuthorizationCredentials з токеном
    :param db: SQLAlchemy сесія
    :param current_user: Поточний користувач
    :return: Повідомлення про успішний вихід
    """
    token = credentials.credentials
    await repository_users.add_to_blacklist(token, db)
    return {"message": USER_IS_LOGOUT}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Оновлення access та refresh токенів.
    - Перевіряє, чи токен співпадає з збереженим у БД.
    - Генерує нові токени.

    :param credentials: HTTPAuthorizationCredentials з refresh токеном
    :param db: SQLAlchemy сесія
    :param current_user: Поточний користувач
    :return: Новий access та refresh токени
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)

    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Підтвердження email за токеном.
    - Перевіряє валідність токена.
    - Позначає email як підтверджений.

    :param token: Токен з листа підтвердження
    :param db: SQLAlchemy сесія
    :return: Повідомлення про статус підтвердження
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=VERIFICATION_ERROR)
    if user.is_verify:
        return {"message": EMAIL_ALREADY_CONFIRMED}

    await repository_users.confirmed_email(email, db)
    return {"message": EMAIL_CONFIRMED}


@router.post('/request_email')
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Повторне відправлення листа для підтвердження email.
    - Якщо email користувача вже підтверджено — повертає повідомлення.
    - Інакше надсилає email асинхронно.

    :param body: RequestEmail з email користувача
    :param background_tasks: Для асинхронної відправки email
    :param request: FastAPI Request для побудови URL
    :param db: SQLAlchemy сесія
    :return: Повідомлення про статус відправки
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVALID_EMAIL)

    if user.is_verify:
        return {"message": EMAIL_CONFIRMED}

    background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": CHECK_YOUR_EMAIL}

async def rate_limiter():
    return True
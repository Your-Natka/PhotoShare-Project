from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.database.models import User
from app.database.connect_db import get_db
from app.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from app.repository import users as repository_users
from app.services.auth import auth_service
from app.conf.messages import (
    ALREADY_EXISTS, EMAIL_ALREADY_CONFIRMED, EMAIL_CONFIRMED,
    EMAIL_NOT_CONFIRMED, INVALID_EMAIL, INVALID_PASSWORD,
    SUCCESS_CREATE_USER, CHECK_YOUR_EMAIL, USER_NOT_ACTIVE,
    USER_IS_LOGOUT, INVALID_TOKEN
)

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors

router = APIRouter(prefix='/auth', tags=["authentication"])
security = HTTPBearer()

# --- Mail configuration ---
conf = ConnectionConfig(
    MAIL_USERNAME="fatsapiuser@meta.ua",
    MAIL_PASSWORD="pythonCourse2023",
    MAIL_FROM="fatsapiuser@meta.ua",
    MAIL_FROM_NAME="PhotoShare Application",
    MAIL_SERVER="smtp.meta.ua",
    MAIL_PORT=465,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """Send confirmation email with token"""
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[str(email)],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification
            },
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="example_email.html")
    except ConnectionErrors as err:
        print("Mail connection error:", err)


# --- Signup ---
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ALREADY_EXISTS)

    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)

    # Відправка листа на підтвердження email
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": SUCCESS_CREATE_USER}


# --- Confirm email ---
@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed")
    if user.is_verify:
        return {"message": EMAIL_ALREADY_CONFIRMED}

    await repository_users.confirmed_email(email, db)
    return {"message": EMAIL_CONFIRMED}


# --- Login ---
@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_EMAIL)
    if not user.is_verify:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=EMAIL_NOT_CONFIRMED)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=USER_NOT_ACTIVE)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_PASSWORD)
    
    access_token = await auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=7200  # 2 години
    )
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# --- Logout ---
@router.post('/logout')
async def logout(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    token = credentials.credentials
    await repository_users.add_to_blacklist(token, db)
    return {"message": USER_IS_LOGOUT}


# --- Refresh token ---
@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
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


# --- Request email verification ---
@router.post('/request_email')
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVALID_EMAIL)
    if user.is_verify:
        return {"message": EMAIL_ALREADY_CONFIRMED}

    background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": CHECK_YOUR_EMAIL}

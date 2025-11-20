import pickle
from typing import Optional

import redis.asyncio as aioredis
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.connect_db import get_db
from app.repository import users as repository_users
from app.conf.config import settings
from app.conf.messages import FAIL_EMAIL_VERIFICATION, INVALID_SCOPE, NOT_VALIDATE_CREDENTIALS

security = HTTPBearer()


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    def __init__(self):
        self.redis_cache = aioredis.from_url(settings.redis_url, decode_responses=False)

    # --- PASSWORD HANDLING ---
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password[:72], hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password[:72])

    # --- TOKEN CREATION ---
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        return self._create_token(data, expires_delta, minutes=15, scope="access_token")

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        return self._create_token(data, expires_delta, days=7, scope="refresh_token")

    def create_email_token(self, data: dict) -> str:
        return self._create_token(data, days=3, scope="email_token")

    def _create_token(self, data: dict, expires_delta: Optional[float] = None, minutes: int = 0, days: int = 0, scope: str = "") -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=minutes, days=days))
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": scope})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    # --- TOKEN DECODING ---
    async def decode_refresh_token(self, refresh_token: str) -> str:
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") != "refresh_token":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_SCOPE)
            return payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=NOT_VALIDATE_CREDENTIALS)

    # --- GET CURRENT USER ---
    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=NOT_VALIDATE_CREDENTIALS)
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") != "access_token":
                raise credentials_exception
            email = payload.get("sub")
            if not email:
                raise credentials_exception

            # Перевірка чорного списку
            black_list_token = await repository_users.find_blacklisted_token(token, db)
            if black_list_token:
                raise credentials_exception

            # Отримання користувача з кешу Redis або БД
            user_data = await self.redis_cache.get(f"user:{email}")
            if user_data:
                user = pickle.loads(user_data)
            else:
                user = await repository_users.get_user_by_email(email, db)
                if not user:
                    raise credentials_exception
                await self.redis_cache.set(f"user:{email}", pickle.dumps(user), ex=900)

            return user

        except JWTError:
            raise credentials_exception

    # --- EMAIL TOKEN ---
    async def get_email_from_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") != "email_token":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_SCOPE)
            return payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=FAIL_EMAIL_VERIFICATION)


auth_service = Auth()
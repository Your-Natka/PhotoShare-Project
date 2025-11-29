import os
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi_limiter import FastAPILimiter
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from fastapi.staticfiles import StaticFiles

from app.conf.config import settings
from app.conf.messages import DB_CONFIG_ERROR, DB_CONNECT_ERROR, WELCOME_MESSAGE
from app.database.connect_db import get_db
from app.routers.auth import router as auth_router
from app.routers.posts import router as post_router
from app.routers.comments import router as comment_router
from app.routers.ratings import router as rating_router
from app.routers.transform_post import router as trans_router
from app.routers.hashtags import router as hashtag_router
from app.routers.users import router as users_router

app = FastAPI(title="Photoshare API", description="API for Photoshare project", version="1.0.0")

# --------------------------------------------
# ROUTERS
# --------------------------------------------
app.include_router(auth_router, prefix='/api')
app.include_router(users_router, prefix='/api')
app.include_router(post_router, prefix='/api')
app.include_router(trans_router, prefix='/api')
app.include_router(hashtag_router, prefix='/api')
app.include_router(comment_router, prefix='/api')
app.include_router(rating_router, prefix='/api')

# --- Статика для медіа ---
# app.mount("/media", StaticFiles(directory=os.path.join("app", "media")), name="media")

# Корінь проєкту (папка, де лежать app та media)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
PROJECT_ROOT = os.path.dirname(BASE_DIR)              # ../ -> PhotoShare-Project

MEDIA_DIR = os.path.join(PROJECT_ROOT, "media")

# Створюємо папки, якщо їх ще немає
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "qrcodes"), exist_ok=True)

# Монтую media
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# --------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------
@app.get("/", name="Project root", tags=["root"])
def read_root():
    """
    Кореневий endpoint для перевірки роботи сервера.

    :return: Привітальне повідомлення
    """
    return {"message": "Hello, Photoshare!"}


# --------------------------------------------
# STARTUP EVENT
# --------------------------------------------
@app.on_event("startup")
async def startup():
    """
    Ініціалізація FastAPILimiter та Redis cache при запуску додатку.

    Використовує REDIS_URL із налаштувань .env.
    Перевіряє доступність Redis через ping.
    """
    redis_cache = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        await redis_cache.ping()  # Перевірка доступності Redis
        print("Redis connected successfully.")
    except Exception as e:
        print(f"Redis connection error: {e}")
        raise

    await FastAPILimiter.init(redis_cache)
    print("FastAPILimiter initialized.")


# --------------------------------------------
# HEALTHCHECKER
# --------------------------------------------
@app.get("/api/healthchecker", tags=["health"])
def healthchecker(db: Session = Depends(get_db)):
    """
    Endpoint для перевірки стану бази даних та доступності сервісу.

    Виконує простий SQL-запит `SELECT 1` для перевірки підключення до DB.
    
    :param db: SQLAlchemy session
    :return: Повідомлення про стан сервісу
    :raises HTTPException: якщо база даних недоступна або запит неуспішний
    """
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail=DB_CONFIG_ERROR)
        return {"message": WELCOME_MESSAGE}
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=DB_CONNECT_ERROR)


# --------------------------------------------
# ENTRYPOINT
# --------------------------------------------
if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)


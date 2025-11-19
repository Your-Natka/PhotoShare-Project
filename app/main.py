import os
import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi_limiter import FastAPILimiter
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.conf.messages import DB_CONFIG_ERROR, DB_CONNECT_ERROR, WELCOME_MESSAGE
from app.database.connect_db import get_db
from app.routes.auth import router as auth_router
from app.routes.posts import router as post_router
from app.routes.comments import router as comment_router
from app.routes.ratings import router as rating_router
from app.routes.transform_post import router as trans_router
from app.routes.hashtags import router as hashtag_router
from app.routes.users import router as users_router
from app.conf.config import settings
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# --- Роутери ---
app.include_router(auth_router, prefix='/api')
app.include_router(users_router, prefix='/api')
app.include_router(post_router, prefix='/api')
app.include_router(trans_router, prefix='/api')
app.include_router(hashtag_router, prefix='/api')
app.include_router(comment_router, prefix='/api')
app.include_router(rating_router, prefix='/api')
# app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/media", StaticFiles(directory=os.path.join("app", "media")), name="media")



# --- Root endpoint ---
@app.get("/", name="Project root")
def read_root():
    return {"message": "Hello, Photoshare!"}


# --- Startup event ---
@app.on_event("startup")
async def startup():
    """
    Ініціалізація  та FastAPILimiter.
    Використовує URL з .env (REDIS_URL).
    """
    redis_cache = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        await redis_cache.ping()  # Перевірка, чи Redis доступний
    except Exception as e:
        print(f"Redis connection error: {e}")
        raise

    await FastAPILimiter.init(redis_cache)


# --- Healthchecker ---
@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail=DB_CONFIG_ERROR)
        return {"message": WELCOME_MESSAGE}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=DB_CONNECT_ERROR)


if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
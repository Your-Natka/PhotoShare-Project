import os
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi_limiter import FastAPILimiter
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.conf.config import settings
from app.conf.messages import DB_CONFIG_ERROR, DB_CONNECT_ERROR, WELCOME_MESSAGE
from app.database.connect_db import get_db
from app.routes.auth import router as auth_router
from app.routes.posts import router as post_router
from app.routes.comments import router as comment_router
from app.routes.ratings import router as rating_router
from app.routes.transform_post import router as trans_router
from app.routes.hashtags import router as hashtag_router
from app.routes.users import router as users_router

# --------------------------------------------
# Lifespan замість on_event
# --------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.conf.config import settings
    import redis.asyncio as redis

    # Моканий Redis під час тестів
    try:
        app.state.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await app.state.redis.ping()
        print("Redis connected successfully.")
    except Exception as e:
        print(f"Redis connection error: {e}")
        app.state.redis = None
    yield
    if app.state.redis:
        await app.state.redis.close()

app = FastAPI(lifespan=lifespan)
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
app.mount("/media", StaticFiles(directory=os.path.join("app", "media")), name="media")

# --------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------
@app.get("/", name="Project root", tags=["root"])
def read_root():
    return {"message": "Hello, Photoshare!"}

# --------------------------------------------
# HEALTHCHECKER
# --------------------------------------------
@app.get("/api/healthchecker", tags=["health"])
def healthchecker(db: Session = Depends(get_db)):
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
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)

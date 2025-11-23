import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_cache = redis.from_url(REDIS_URL)

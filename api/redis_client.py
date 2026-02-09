import os
from redis.asyncio import Redis, from_url

REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


def _build_redis_url() -> str:
    if REDIS_URL:
        if REDIS_PASSWORD and "@" not in REDIS_URL:
            # inject password into URL if missing
            if REDIS_URL.startswith("redis://"):
                return REDIS_URL.replace("redis://", f"redis://:{REDIS_PASSWORD}@", 1)
        return REDIS_URL

    if REDIS_PASSWORD:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    return f"redis://{REDIS_HOST}:{REDIS_PORT}/0"


redis_client: Redis = from_url(_build_redis_url(), decode_responses=True)

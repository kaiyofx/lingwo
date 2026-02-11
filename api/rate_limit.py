"""
Ограничение запросов к модели (проверка темы, оценка сочинения) на пользователя.
Скользящее окно 60 секунд, по умолчанию не более 30 запросов в минуту.
"""
import logging
import time
from fastapi import HTTPException

from api.redis_client import redis_client

logger = logging.getLogger(__name__)

# запросов в минуту на одного пользователя
MODEL_RATE_LIMIT_PER_MINUTE = int(__import__("os").environ.get("MODEL_RATE_LIMIT_PER_MINUTE", "30"))
RATE_LIMIT_WINDOW_SEC = 60
REDIS_KEY_PREFIX = "ratelimit:model:"


async def check_model_rate_limit(user_id: str) -> None:
    """
    Увеличивает счётчик запросов к модели для user_id и при превышении лимита
    выбрасывает HTTPException 429. Использует скользящее окно в Redis (sorted set).
    """
    key = f"{REDIS_KEY_PREFIX}{user_id}"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SEC
    member = f"{now}"

    pipe = redis_client.pipeline()
    pipe.zadd(key, {member: now})
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.expire(key, RATE_LIMIT_WINDOW_SEC + 1)
    results = await pipe.execute()
    count = results[2] or 0

    if count > MODEL_RATE_LIMIT_PER_MINUTE:
        await redis_client.zrem(key, member)
        logger.warning("model rate limit exceeded for user_id=%s (count=%s)", user_id, count)
        raise HTTPException(
            status_code=429,
            detail=f"Превышен лимит запросов к проверке темы и оценке сочинений: не более {MODEL_RATE_LIMIT_PER_MINUTE} в минуту. Попробуйте позже.",
        )

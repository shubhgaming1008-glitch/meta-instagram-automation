"""
Redis client for caching, idempotency locks, and rate-limit tracking.
"""
import redis.asyncio as aioredis

from app.core.config import settings

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get the shared async Redis client."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def acquire_lock(key: str, expire_seconds: int = 30) -> bool:
    """Try to acquire a distributed lock. Returns True if acquired."""
    r = await get_redis()
    return await r.set(f"lock:{key}", "1", nx=True, ex=expire_seconds)


async def release_lock(key: str) -> None:
    r = await get_redis()
    await r.delete(f"lock:{key}")


async def is_event_processed(event_id: str) -> bool:
    """Check if a webhook event ID has already been processed (deduplication)."""
    r = await get_redis()
    return bool(await r.exists(f"event:{event_id}"))


async def mark_event_processed(event_id: str, ttl_seconds: int = 86400) -> None:
    """Mark a webhook event as processed with a 24h TTL."""
    r = await get_redis()
    await r.set(f"event:{event_id}", "1", ex=ttl_seconds)


async def increment_rate_counter(key: str, window_seconds: int) -> int:
    """Increment a rate counter. Returns current count."""
    r = await get_redis()
    pipe = r.pipeline()
    await pipe.incr(f"rate:{key}")
    await pipe.expire(f"rate:{key}", window_seconds)
    results = await pipe.execute()
    return results[0]

"""Redis-backed request rate limiting.

Each limited route gets a fixed-window counter in Redis (INCR + EXPIRE),
shared across every worker/replica pointed at the same Redis instance. If
Redis is unreachable, the limiter falls back to a per-process in-memory
window instead of raising -- a Redis outage should degrade fairness across
replicas, not turn into a 500 on every rate-limited request.
"""

import logging
import time
from collections import defaultdict, deque

import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None
_redis_down = False


def _client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


# key -> timestamps of recent requests, oldest first. Only consulted while
# Redis is down, so it never needs to be shared across processes.
_local_windows: dict[str, deque] = defaultdict(deque)


def _allow_locally(key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    hits = _local_windows[key]
    while hits and hits[0] <= now - window_seconds:
        hits.popleft()
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


async def _allow_in_redis(key: str, limit: int, window_seconds: int) -> bool:
    r = _client()
    window = int(time.time() // window_seconds)
    redis_key = f"ratelimit:{key}:{window}"
    count = await r.incr(redis_key)
    if count == 1:
        await r.expire(redis_key, window_seconds)
    return count <= limit


def rate_limit(name: str, limit: int, window_seconds: int = 60):
    """FastAPI dependency: allow `limit` requests per `window_seconds` per
    client IP. `name` is a stable identifier for the route -- use a fixed
    string rather than request.url.path, which varies per session_id on
    routes like finalize and would give every session its own bucket."""

    async def dependency(request: Request) -> None:
        global _redis_down
        client_ip = request.client.host if request.client else "unknown"
        key = f"{name}:{client_ip}"
        try:
            allowed = await _allow_in_redis(key, limit, window_seconds)
            if _redis_down:
                logger.info("Redis reachable again - resuming shared rate limiting")
                _redis_down = False
        except Exception as e:
            if not _redis_down:
                logger.warning(f"Redis unreachable for rate limiting, falling back to in-memory: {e}")
            _redis_down = True
            allowed = _allow_locally(key, limit, window_seconds)

        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    return dependency

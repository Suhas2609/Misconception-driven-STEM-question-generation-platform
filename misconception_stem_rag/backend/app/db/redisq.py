"""Redis queue helpers."""

from __future__ import annotations

from typing import Any, Optional

import redis.asyncio as redis

from ..config import get_settings

_client: Optional[redis.Redis] = None


def get_client() -> redis.Redis:
    """Return a lazily initialised Redis client."""

    global _client  # noqa: PLW0603 - module level singleton
    if _client is None:
        settings = get_settings()
        _client = redis.Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _client


async def enqueue(queue_name: str, item: Any) -> None:
    client = get_client()
    await client.lpush(queue_name, item)


async def dequeue(queue_name: str) -> Any:
    client = get_client()
    return await client.rpop(queue_name)


async def close_client() -> None:
    global _client  # noqa: PLW0603 - module level singleton
    if _client is not None:
        await _client.close()
        _client = None

from typing import Any

from redis import asyncio as redis_async

from app.config import get_settings

_settings = get_settings()
_client: redis_async.Redis | None = None


def get_client() -> redis_async.Redis:
    global _client
    if _client is None:
        _client = redis_async.from_url(_settings.redis_url, decode_responses=True)
    return _client


async def enqueue(queue_name: str, item: Any) -> None:
    client = get_client()
    await client.lpush(queue_name, item)


async def dequeue(queue_name: str) -> Any:
    client = get_client()
    result = await client.rpop(queue_name)
    return result


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None

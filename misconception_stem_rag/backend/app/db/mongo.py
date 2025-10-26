"""MongoDB client helpers."""

from __future__ import annotations

from typing import Any, AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from ..config import get_settings

_client: Any = None


def get_client() -> AsyncIOMotorClient:
    """Return a singleton MongoDB client using lazy initialisation."""

    global _client  # noqa: PLW0603 - module level singleton
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Return the configured database from MongoDB."""

    settings = get_settings()
    return get_client()[settings.database_name]


def get_collection(name: str) -> AsyncIOMotorCollection:
    """Convenience helper for retrieving a collection by name."""

    return get_database()[name]


async def yield_collection(name: str) -> AsyncIterator[AsyncIOMotorCollection]:
    """Dependency wrapper yielding a collection for FastAPI routes."""

    collection = get_collection(name)
    try:
        yield collection
    finally:
        # Motor handles connection pooling automatically; nothing to close here.
        return

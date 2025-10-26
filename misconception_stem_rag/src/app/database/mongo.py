from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticCollection, AgnosticDatabase

from app.config import get_settings

_settings = get_settings()
_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(_settings.mongodb_url)
    return _client


def get_database() -> AgnosticDatabase:
    return get_client()[_settings.database_name]


def get_collection(name: str) -> AgnosticCollection:
    return get_database()[name]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None

"""ChromaDB helper utilities."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from ..config import get_settings

_settings = get_settings()
_client: ClientAPI | None = None


def get_client() -> ClientAPI:
    """Return a persistent Chroma client singleton."""

    global _client  # noqa: PLW0603 - module level singleton
    if _client is None:
        _client = chromadb.PersistentClient(path=_settings.chromadb_path)
    return _client


def get_collection(name: str) -> Collection:
    """Fetch or create a collection using a sentence transformer embedder."""

    client = get_client()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_or_create_collection(name=name, embedding_function=embedding_fn)


def reset_collection(name: str) -> None:
    """Drop and recreate the named collection."""

    client = get_client()
    if name in {collection.name for collection in client.list_collections()}:
        client.delete_collection(name)
    client.get_or_create_collection(name=name)


def add_document(
    collection_name: str,
    document_id: str,
    document: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Upsert a single document into a collection."""

    collection = get_collection(collection_name)
    collection.upsert(
        ids=[document_id],
        documents=[document],
        metadatas=[metadata or {}],
    )

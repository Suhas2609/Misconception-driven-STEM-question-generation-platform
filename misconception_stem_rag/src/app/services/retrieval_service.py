"""ChromaDB retrieval utilities."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from app.database import chroma

_COLLECTION_NAME = "factual_content"


def _get_collection(name: str = _COLLECTION_NAME):
    return chroma.get_collection(name)


def add_to_chroma(docs: Iterable[dict[str, Any]], collection_name: str = _COLLECTION_NAME) -> None:
    collection = _get_collection(collection_name)
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for index, doc in enumerate(docs):
        content = doc.get("text") or doc.get("content")
        if not content:
            continue
        doc_id = doc.get("id") or f"doc_{index}"
        ids.append(str(doc_id))
        documents.append(str(content))
        metadatas.append(doc.get("metadata", {}))

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def retrieve_from_chroma(
    query: str,
    collection_name: str = _COLLECTION_NAME,
    limit: int = 3,
) -> dict[str, Any]:
    if not query:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    collection = _get_collection(collection_name)
    try:
        return collection.query(query_texts=[query], n_results=limit)
    except Exception:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


def retrieve_context(query: str, limit: int = 3) -> dict[str, Any]:
    return retrieve_from_chroma(query, collection_name=_COLLECTION_NAME, limit=limit)


def flatten_documents(result: dict[str, Any]) -> list[str]:
    documents: Sequence[Sequence[str]] = result.get("documents", [[]])
    if not documents:
        return []
    return [doc for batch in documents for doc in batch if doc]

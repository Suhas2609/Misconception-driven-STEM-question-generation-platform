"""PDF ingestion helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nltk
import pymupdf
import pymupdf4llm

_NLTK_DOWNLOAD_LOCKED = False


def _ensure_nltk() -> None:
    global _NLTK_DOWNLOAD_LOCKED  # noqa: PLW0603 - module level flag
    if _NLTK_DOWNLOAD_LOCKED:
        return
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:  # pragma: no cover - only runs once
        nltk.download("punkt")
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:  # pragma: no cover - only runs once
        nltk.download("punkt_tab")
    _NLTK_DOWNLOAD_LOCKED = True


def _load_pdf(path: Path) -> Any:
    try:
        return pymupdf4llm.load(path)
    except Exception:  # pragma: no cover - fallback path
        return pymupdf.open(path)


def _chunk_text(text: str, max_tokens: int = 500) -> list[str]:
    if not text:
        return []

    _ensure_nltk()
    sentences = nltk.sent_tokenize(text)
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for sentence in sentences:
        token_count = len(sentence.split())
        if current_length + token_count > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk).strip())
            current_chunk = [sentence]
            current_length = token_count
        else:
            current_chunk.append(sentence)
            current_length += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    return [chunk for chunk in chunks if chunk]


def process_pdf(file_path: str) -> list[str]:
    """Load a PDF and return token-aware text chunks."""

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found at {path}")

    document = _load_pdf(path)
    try:
        pages = [page.get_text("text") for page in document]
    except AttributeError:  # pragma: no cover - for pymupdf4llm responses
        pages = [page.page_content for page in document]

    full_text = " ".join(fragment.strip() for fragment in pages if fragment)
    return _chunk_text(full_text)

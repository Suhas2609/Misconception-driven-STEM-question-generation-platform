"""Validation helpers for question payloads and misconception templates."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from textwrap import dedent

from pydantic import ValidationError

from ..db import chroma
from ..models.question import QuestionModel
from . import retrieval
from ..config import get_settings
from openai import OpenAI

_MISCONCEPTION_COLLECTION = "misconceptions"
_MISCONCEPTION_DIR = Path("data/misconceptions")
_misconception_cache: list[dict[str, Any]] | None = None
_misconceptions_seeded = False


def parse_question_payload(payload: Any) -> QuestionModel:
    """Parse arbitrary payloads into a validated QuestionModel instance."""

    data: Any
    if isinstance(payload, QuestionModel):
        return payload
    if isinstance(payload, str):
        data = json.loads(payload)
    elif isinstance(payload, dict):
        data = payload
    else:
        raise TypeError("Unsupported payload type for question parsing")

    try:
        return QuestionModel.model_validate(data)
    except ValidationError as exc:  # pragma: no cover - depends on pydantic internals
        raise ValueError("Question payload validation failed") from exc


def ensure_valid_question(payload: Any) -> dict[str, Any]:
    question = parse_question_payload(payload)
    return question.model_dump()


def _load_misconception_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not _MISCONCEPTION_DIR.exists():
        return rows

    for csv_path in sorted(_MISCONCEPTION_DIR.glob("*.csv")):
        with csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for index, raw_row in enumerate(reader):
                row = {
                    "subject": (raw_row.get("subject") or "").strip(),
                    "concept": (raw_row.get("concept") or "").strip(),
                    "misconception_text": (raw_row.get("misconception_text") or "").strip(),
                    "correction": (raw_row.get("correction") or "").strip(),
                }
                if any(row.values()):
                    row["id"] = raw_row.get("id") or f"{csv_path.stem}-{index}"
                    rows.append(row)
    return rows


def _seed_misconceptions(force: bool = False) -> None:
    global _misconception_cache, _misconceptions_seeded  # noqa: PLW0603 - module level cache
    if _misconceptions_seeded and not force:
        return

    rows = _load_misconception_rows()
    if not rows:
        _misconception_cache = []
        _misconceptions_seeded = True
        return

    documents = []
    for row in rows:
        content = (
            f"Subject: {row['subject']}\n"
            f"Concept: {row['concept']}\n"
            f"Misconception: {row['misconception_text']}\n"
            f"Correction: {row['correction']}"
        )
        documents.append(
            {
                "id": row["id"],
                "text": content,
                "metadata": {
                    "subject": row["subject"],
                    "concept": row["concept"],
                    "misconception_text": row["misconception_text"],
                    "correction": row["correction"],
                },
            }
        )

    chroma.reset_collection(_MISCONCEPTION_COLLECTION)
    retrieval.add_to_chroma(documents, collection_name=_MISCONCEPTION_COLLECTION)
    _misconception_cache = rows
    _misconceptions_seeded = True


def get_related_misconceptions(topic: str, limit: int = 3) -> list[dict[str, Any]]:
    if not topic:
        return []

    _seed_misconceptions()
    if not _misconception_cache:
        return []

    results = retrieval.retrieve_from_chroma(
        topic,
        collection_name=_MISCONCEPTION_COLLECTION,
        limit=limit,
    )

    ids = results.get("ids", [[]])[0] if results.get("ids") else []
    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    related: list[dict[str, Any]] = []
    for idx, meta in enumerate(metadatas):
        if not meta:
            continue
        entry = {
            "id": ids[idx] if idx < len(ids) else None,
            "subject": meta.get("subject"),
            "concept": meta.get("concept"),
            "misconception_text": meta.get("misconception_text"),
            "correction": meta.get("correction"),
            "document": documents[idx] if idx < len(documents) else None,
            "distance": distances[idx] if idx < len(distances) else None,
        }
        related.append(entry)
    return related


def synthesize_misconceptions(document_text: str, n: int = 3) -> list[str]:
    """Use the LLM to synthesise likely misconceptions from a document's text.

    Returns a list of short misconception strings. If OpenAI key is unavailable
    returns an empty list.
    """

    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key or "REDACTED" in api_key:
        return []

    client = OpenAI(api_key=api_key)
    prompt = dedent(
        f"""
        You will receive STEM source material. Analyse it and produce the top {n} plausible learner misconceptions.

        Requirements:
        - Each misconception must be a single declarative sentence that sounds plausible yet incorrect.
        - Focus on errors that a well-meaning student might make after reading the passage.
        - Provide a concise note explaining why the misconception feels reasonable and the corrective focus required.

        Return a JSON object of the form:
        {{
          "misconceptions": [
            {{
              "statement": "...",
              "why_plausible": "...",
              "corrective_focus": "..."
            }}
          ]
        }}

        Source passage:
        {document_text.strip()}
        """
    )

    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an educational data miner. Respond only with valid JSON and never include prose or markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        resp = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            messages=messages,
            temperature=0.15,
        )
        content = resp.choices[0].message.content
        if not content:
            return []

        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "misconceptions" in parsed:
                candidates = parsed.get("misconceptions", [])
            elif isinstance(parsed, list):
                candidates = parsed
            else:
                candidates = []

            cleaned: list[str] = []
            for item in candidates:
                if isinstance(item, dict):
                    text = item.get("statement") or item.get("misconception") or item.get("text")
                else:
                    text = str(item)
                if text:
                    cleaned.append(str(text).strip())
                if len(cleaned) == n:
                    break
            return cleaned
        except Exception:
            lines = [ln.strip().lstrip("- ") for ln in content.splitlines() if ln.strip()]
            return [l for l in lines][:n]
    except Exception:
        return []

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


def get_related_misconceptions(
    topic: str, 
    limit: int = 3,
    domain: str | None = None,
    subject: str | None = None,
    topic_relevance_threshold: float = 0.7
) -> list[dict[str, Any]]:
    """
    Retrieve misconceptions related to a topic with domain and topic-level filtering.
    
    Args:
        topic: Topic name or description to search for
        limit: Maximum number of misconceptions to return
        domain: Optional domain filter (e.g., "Physics", "Chemistry")
        subject: Optional subject filter (alias for domain)
        topic_relevance_threshold: Minimum similarity score (0-1) for topic relevance
                                   Lower distance = higher similarity
                                   Default 0.7 = strong topic alignment required
        
    Returns:
        List of misconception dictionaries with metadata
        
    CRITICAL FILTERING (TWO-LEVEL):
    1. DOMAIN-LEVEL: When domain/subject is provided, ONLY retrieves from that domain
       (prevents Physics misconceptions in Chemistry questions)
    2. TOPIC-LEVEL: Filters by semantic similarity to specific topic
       (prevents "Organic Chemistry" misconceptions in "Chemical Bonding" questions)
       (prevents "Thermodynamics" misconceptions in "Newton's Laws" questions)
    """
    if not topic:
        return []

    _seed_misconceptions()
    if not _misconception_cache:
        return []

    # Use subject as fallback for domain
    filter_domain = domain or subject
    
    # Build where filter for domain-specific retrieval
    where_filter = None
    if filter_domain:
        where_filter = {"subject": filter_domain}
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 [DOMAIN FILTER] Retrieving {filter_domain} misconceptions only")

    # TOPIC-LEVEL FILTERING: Retrieve MORE candidates initially (3x limit)
    # so we have enough after topic relevance filtering
    initial_limit = min(limit * 5, 15)  # Get 5x candidates but cap at 15
    
    results = retrieval.retrieve_from_chroma(
        topic,
        collection_name=_MISCONCEPTION_COLLECTION,
        limit=initial_limit,
        where=where_filter,
    )

    ids = results.get("ids", [[]])[0] if results.get("ids") else []
    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    import logging
    logger = logging.getLogger(__name__)

    related: list[dict[str, Any]] = []
    filtered_count = 0
    
    for idx, meta in enumerate(metadatas):
        if not meta:
            continue
        
        # LEVEL 1: DOMAIN VALIDATION - Reject cross-domain misconceptions
        misconception_subject = meta.get("subject", "")
        if filter_domain and misconception_subject != filter_domain:
            logger.error(
                f"🚨 DOMAIN VIOLATION: Expected {filter_domain}, "
                f"got {misconception_subject} for misconception: "
                f"{meta.get('misconception_text', '')[:60]}..."
            )
            continue  # Skip this misconception
        
        # LEVEL 2: TOPIC RELEVANCE - Filter by semantic similarity to topic
        # ChromaDB returns distances where SMALLER = MORE SIMILAR
        # Convert distance to similarity: similarity = 1 - (distance / 2)
        # (assuming L2 distance normalized to [0, 2])
        distance = distances[idx] if idx < len(distances) else 1.0
        similarity = 1.0 - (min(distance, 2.0) / 2.0)  # Normalize to [0, 1]
        
        if similarity < topic_relevance_threshold:
            filtered_count += 1
            misconception_text = meta.get('misconception_text', '')[:60]
            logger.debug(
                f"🔍 [TOPIC FILTER] Excluded low-relevance misconception "
                f"(similarity={similarity:.3f} < {topic_relevance_threshold}): "
                f"{misconception_text}..."
            )
            continue  # Skip misconceptions with low topic relevance
            
        entry = {
            "id": ids[idx] if idx < len(ids) else None,
            "subject": misconception_subject,
            "concept": meta.get("concept"),
            "misconception_text": meta.get("misconception_text"),
            "correction": meta.get("correction"),
            "document": documents[idx] if idx < len(documents) else None,
            "distance": distance,
            "similarity": similarity,  # Add similarity score for debugging
        }
        related.append(entry)
        
        # Stop once we have enough highly relevant misconceptions
        if len(related) >= limit:
            break
    
    if filter_domain:
        logger.info(
            f"✅ [TOPIC FILTER] Retrieved {len(related)}/{initial_limit} {filter_domain} "
            f"misconceptions for topic '{topic}' "
            f"(filtered {filtered_count} low-relevance, threshold={topic_relevance_threshold})"
        )
    else:
        logger.info(
            f"✅ [TOPIC FILTER] Retrieved {len(related)}/{initial_limit} misconceptions "
            f"for topic '{topic}' (filtered {filtered_count} low-relevance)"
        )
    
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

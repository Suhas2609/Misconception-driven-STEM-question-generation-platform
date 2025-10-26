"""Routes for PDF ingestion."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, Query, status

from ..db import mongo
from ..services import pdf as pdf_service
from ..services import retrieval as retrieval_service
from ..services import generation as generation_service
from ..services import validation as validation_service
from ..services import cognitive as cognitive_service

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str | None = Query(None),
    topic: str | None = Query(None),
    num_questions: int = Query(3, ge=1, le=10),
) -> dict[str, Any]:
    """Upload a PDF, ingest text into Chroma, generate questions, persist to Mongo, and return them.

    Optional query params:
    - user_id: owner/creator id for questions
    - topic: topic label used for retrieval of misconceptions
    - num_questions: how many questions to generate (1-10)
    """

    destination_dir = Path("data/pdfs")
    destination_dir.mkdir(parents=True, exist_ok=True)
    file_path = destination_dir / file.filename

    try:
        contents = await file.read()
        file_path.write_bytes(contents)
        chunks = pdf_service.process_pdf(str(file_path))
    except Exception as exc:  # pragma: no cover - surfaced via HTTP details
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not chunks:
        return {"filename": file.filename, "num_chunks": 0, "questions": []}

    # Add chunks to Chroma for later retrieval
    docs = []
    for idx, chunk in enumerate(chunks):
        docs.append({
            "id": f"{file_path.stem}-{idx}",
            "text": chunk,
            "metadata": {"source": file.filename, "index": idx},
        })

    try:
        retrieval_service.add_to_chroma(docs, collection_name="factual_content")
    except Exception:
        # non-fatal: continue even if indexing fails
        pass

    # Prepare for question generation
    questions: list[dict[str, Any]] = []
    questions_collection = mongo.get_collection("questions")

    # derive related misconceptions for the provided topic or filename
    related_miscs = validation_service.get_related_misconceptions(topic or file.filename)
    related_texts = [item.get("misconception_text") for item in related_miscs if item.get("misconception_text")]

    # baseline cognitive traits
    traits = cognitive_service.init_profile().model_dump()

    # generate questions using successive chunks as contexts
    for i in range(num_questions):
        # simple strategy: combine a few neighbouring chunks to make richer context
        start = (i * 1) % len(chunks)
        end = min(start + 3, len(chunks))
        fact_context = "\n".join(chunks[start:end])

        try:
            raw_question = generation_service.generate_question(
                fact_context=fact_context,
                misconceptions=[m for m in (related_texts or [])],
                traits=traits,
            )
        except Exception:
            raw_question = None

        if not raw_question or not isinstance(raw_question, dict):
            continue

        question_payload: dict[str, Any] = dict(raw_question)
        # ensure fields exist
        question_payload["topic"] = topic or file.filename
        question_payload["user_id"] = user_id or "system"
        question_payload.setdefault("id", str(uuid4()))
        question_payload["timestamp"] = datetime.utcnow()

        try:
            question_model = validation_service.parse_question_payload(question_payload)
        except Exception:
            # skip invalid payloads
            continue

        document = question_model.model_dump()
        identifier = document.get("id")
        document["_id"] = identifier

        try:
            await questions_collection.update_one({"_id": identifier}, {"$set": document}, upsert=True)
        except Exception:
            # persist failure shouldn't block returning generated results
            pass

        questions.append(document)

    return {
        "filename": file.filename,
        "num_chunks": len(chunks),
        "questions_generated": len(questions),
        "questions": questions,
    }

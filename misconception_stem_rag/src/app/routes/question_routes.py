import logging
from datetime import datetime
from typing import Any, Mapping
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from motor.core import AgnosticCollection
from pymongo.errors import PyMongoError

from app.database import mongo
from app.models.question_model import QuestionModel, QuestionRequest, QuestionResponse
from app.services import (
    cognitive_service,
    generation_service,
    retrieval_service,
    validation_service,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _user_collection() -> AgnosticCollection:
    return mongo.get_collection("users")


def _question_collection() -> AgnosticCollection:
    return mongo.get_collection("questions")


async def _load_user_traits(
    user_id: str,
    trait_overrides: Mapping[str, Any] | None,
    collection: AgnosticCollection | None,
):
    stored_traits: Mapping[str, Any] = {}
    if collection is not None:
        try:
            user_doc = await collection.find_one({"_id": user_id}) or await collection.find_one(
                {"email": user_id}
            )
            if user_doc:
                stored_traits = user_doc.get("cognitive_traits", {})
        except PyMongoError:
            logger.warning("Unable to load traits for user %s", user_id, exc_info=True)
        except Exception:
            logger.warning("Unexpected error when loading traits for user %s", user_id, exc_info=True)

    merged_traits = dict(stored_traits)
    if trait_overrides:
        merged_traits.update(trait_overrides)
    return cognitive_service.derive_traits(merged_traits)


async def _persist_question(
    question: QuestionModel,
    collection: AgnosticCollection | None,
) -> None:
    if collection is None:
        return

    document = question.model_dump()
    identifier = document.get("id") or str(uuid4())
    document["id"] = identifier
    document["_id"] = identifier

    try:
        await collection.update_one({"_id": identifier}, {"$set": document}, upsert=True)
    except PyMongoError:
        logger.warning("Failed to persist question %s", identifier, exc_info=True)
    except Exception:
        logger.warning("Unexpected error while persisting question %s", identifier, exc_info=True)


@router.post("/generate", response_model=QuestionResponse)
async def generate_question(
    payload: QuestionRequest,
    question_collection: AgnosticCollection | None = Depends(_question_collection),
    user_collection: AgnosticCollection | None = Depends(_user_collection),
) -> QuestionResponse:
    retrieval_result = retrieval_service.retrieve_context(payload.topic)
    documents = retrieval_service.flatten_documents(retrieval_result)
    fact_context = payload.factual_context or " ".join(documents) or "No context available."

    traits = await _load_user_traits(payload.user_id, payload.traits, user_collection)

    related_misconceptions = validation_service.get_related_misconceptions(payload.topic)
    related_texts = [item.get("misconception_text") for item in related_misconceptions]

    combined_misconceptions: list[str] = []
    for source in (payload.misconceptions, related_texts):
        for item in source or []:
            if item and item not in combined_misconceptions:
                combined_misconceptions.append(item)

    raw_question = generation_service.generate_question(
        fact_context=fact_context,
        misconceptions=combined_misconceptions,
        traits=traits.model_dump(),
    )

    if not isinstance(raw_question, dict):
        raise HTTPException(status_code=502, detail="Generator returned unsupported payload")

    question_payload: dict[str, Any] = dict(raw_question)

    if "difficulty" not in question_payload and "estimated_difficulty" in question_payload:
        question_payload["difficulty"] = question_payload.pop("estimated_difficulty")

    question_payload["topic"] = payload.topic
    question_payload["user_id"] = payload.user_id
    question_payload.setdefault("id", str(uuid4()))
    question_payload["timestamp"] = datetime.utcnow()

    try:
        question_model = validation_service.parse_question_payload(question_payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    await _persist_question(question_model, question_collection)

    return QuestionResponse.model_validate(question_model.model_dump())

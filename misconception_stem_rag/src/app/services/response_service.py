"""Service layer for handling learner responses and analytics."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from motor.core import AgnosticCollection
from pymongo.errors import PyMongoError
from redis.exceptions import RedisError

from app.database import redisq
from app.models.response_model import ResponseSubmission
from app.models.user_model import CognitiveTraits
from app.services import cognitive_service

logger = logging.getLogger(__name__)

_RESPONSE_QUEUE = "response_events"


class ResponseServiceError(Exception):
    """Base error raised by the response service."""


class QuestionNotFoundError(ResponseServiceError):
    """Raised when the referenced question cannot be located."""


class OptionMismatchError(ResponseServiceError):
    """Raised when the selected option does not exist on the question."""


class PersistenceError(ResponseServiceError):
    """Raised when the response cannot be persisted."""


def _extract_option_type(question: Mapping[str, Any], selected_option: str) -> str | None:
    options = question.get("options") or []
    for option in options:
        if option.get("text") == selected_option:
            return str(option.get("type", "")).lower()
    return None


def _derive_trait_feedback(option_type: str, confidence: float) -> Mapping[str, float]:
    option_type = option_type.lower()
    if option_type == "correct":
        precision = 0.9
        analytical_depth = 0.85
    elif option_type == "partial":
        precision = 0.65
        analytical_depth = 0.6
    elif option_type == "procedural":
        precision = 0.55
        analytical_depth = 0.5
    else:  # misconception or unknown
        precision = 0.35
        analytical_depth = 0.4

    return {
        "precision": precision,
        "confidence": max(0.0, min(1.0, confidence)),
        "analytical_depth": analytical_depth,
    }


async def process_response(
    submission: ResponseSubmission,
    responses_collection: AgnosticCollection | None,
    questions_collection: AgnosticCollection | None,
) -> CognitiveTraits:
    """Persist a learner's response, enqueue analytics, and update traits."""

    if questions_collection is None:
        raise QuestionNotFoundError("Question store unavailable")

    try:
        question_doc = await questions_collection.find_one({"_id": submission.question_id})
        if not question_doc:
            question_doc = await questions_collection.find_one({"id": submission.question_id})
    except PyMongoError as exc:  # pragma: no cover - defensive, depends on backend state
        logger.error("Failed to fetch question %s", submission.question_id, exc_info=True)
        raise QuestionNotFoundError("Unable to retrieve question metadata") from exc

    if not question_doc:
        raise QuestionNotFoundError("Question not found")

    option_type = _extract_option_type(question_doc, submission.selected_option)
    if option_type is None:
        raise OptionMismatchError("Selected option not recognised for question")

    created_at = datetime.utcnow()
    response_id = str(uuid4())
    record = {
        "id": response_id,
        "user_id": submission.user_id,
        "question_id": submission.question_id,
        "selected_option": submission.selected_option,
        "option_type": option_type,
        "confidence": float(submission.confidence),
        "reasoning": submission.reasoning,
        "is_correct": option_type == "correct",
        "created_at": created_at,
    }

    if responses_collection is None:
        raise PersistenceError("Response store unavailable")

    doc = dict(record)
    doc["_id"] = response_id

    try:
        await responses_collection.insert_one(doc)
    except PyMongoError as exc:  # pragma: no cover - defensive
        logger.error("Failed to persist response %s", response_id, exc_info=True)
        raise PersistenceError("Unable to save response") from exc

    feedback = _derive_trait_feedback(option_type, submission.confidence)
    try:
        updated_traits = await cognitive_service.update_traits(submission.user_id, feedback)
    except ValueError as exc:
        raise PersistenceError(str(exc)) from exc

    event_payload = {
        "response_id": response_id,
        "user_id": submission.user_id,
        "question_id": submission.question_id,
        "option_type": option_type,
        "confidence": float(submission.confidence),
        "is_correct": option_type == "correct",
        "created_at": created_at.isoformat(),
    }

    try:
        await redisq.enqueue(_RESPONSE_QUEUE, json.dumps(event_payload))
    except (RedisError, ConnectionError):  # pragma: no cover - external system failure
        logger.warning("Failed to enqueue response analytics event", exc_info=True)

    return updated_traits


__all__ = [
    "process_response",
    "ResponseServiceError",
    "QuestionNotFoundError",
    "OptionMismatchError",
    "PersistenceError",
]

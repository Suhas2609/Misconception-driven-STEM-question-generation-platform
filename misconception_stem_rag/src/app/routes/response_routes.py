"""Routes for capturing learner responses."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from motor.core import AgnosticCollection

from app.database import mongo
from app.models.response_model import ResponseSubmission, TraitSummary
from app.services import response_service

router = APIRouter()
logger = logging.getLogger(__name__)


def _responses_collection() -> AgnosticCollection:
    return mongo.get_collection("responses")


def _questions_collection() -> AgnosticCollection:
    return mongo.get_collection("questions")


@router.post("/submit", response_model=TraitSummary, status_code=status.HTTP_200_OK)
async def submit_response(
    payload: ResponseSubmission,
    responses_collection: AgnosticCollection = Depends(_responses_collection),
    questions_collection: AgnosticCollection = Depends(_questions_collection),
) -> TraitSummary:
    try:
        updated_traits = await response_service.process_response(
            payload,
            responses_collection,
            questions_collection,
        )
    except response_service.QuestionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except response_service.OptionMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except response_service.PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except response_service.ResponseServiceError as exc:
        logger.error("Unexpected response service error", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return TraitSummary(user_id=payload.user_id, traits=updated_traits)

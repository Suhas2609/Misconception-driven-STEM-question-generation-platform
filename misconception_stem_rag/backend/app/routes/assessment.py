"""Assessment routes for cognitive profiling during onboarding."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.assessment import AssessmentQuestion, get_assessment_questions
from ..models.user import UserModel
from ..routes.auth import get_current_user
from ..db.mongo import get_collection
from ..services.assessment import score_assessment_responses

router = APIRouter()
logger = logging.getLogger(__name__)


class AssessmentResponse(BaseModel):
    """User's answer to a single assessment question."""

    question_id: str
    answer_text: str
    confidence: float | None = None


class AssessmentSubmission(BaseModel):
    """Complete set of assessment responses."""

    responses: list[AssessmentResponse]


def _user_collection():
    return get_collection("users")


@router.get("/questions", response_model=list[AssessmentQuestion])
async def get_questions() -> list[AssessmentQuestion]:
    """Return the cognitive assessment question set for onboarding."""
    return get_assessment_questions()


@router.post("/submit", response_model=UserModel)
async def submit_assessment(
    submission: AssessmentSubmission,
    current_user: UserModel = Depends(get_current_user),
    collection=Depends(_user_collection),
) -> UserModel:
    """
    Score the user's assessment responses using AI, update cognitive traits, and mark onboarding complete.
    """
    logger.info(f"📥 Assessment submission received from user {current_user.id} ({current_user.email})")
    logger.info(f"📊 Number of responses: {len(submission.responses)}")
    
    # Convert Pydantic models to dicts for scoring service
    response_dicts = [resp.model_dump() for resp in submission.responses]
    
    # Use LLM to derive cognitive trait scores from free-form reasoning
    logger.info("🧠 Calling GPT-4o to score cognitive traits...")
    scored_traits = score_assessment_responses(response_dicts)
    
    logger.info(f"✅ Traits scored: {scored_traits.model_dump()}")
    
    # Update user record with new traits and mark onboarding complete
    await collection.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "cognitive_traits": scored_traits.model_dump(),
                "onboarding_completed": True,
            }
        },
    )
    
    logger.info(f"💾 Updated user {current_user.id} with new traits and onboarding_completed=True")

    updated_doc = await collection.find_one({"_id": current_user.id})
    if not updated_doc:
        raise HTTPException(status_code=404, detail="User not found after update")

    logger.info(f"✅ Assessment complete for {current_user.email}")
    return UserModel(**updated_doc)

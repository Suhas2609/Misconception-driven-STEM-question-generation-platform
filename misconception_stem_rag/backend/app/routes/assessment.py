"""Assessment routes for cognitive profiling during onboarding."""

from __future__ import annotations

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..models.assessment import AssessmentQuestion, get_assessment_questions
from ..models.user import UserModel
from ..routes.auth import get_current_user
from ..db.mongo import get_collection
from ..services.assessment import score_assessment_responses
from ..services.cognitive_trait_update import CognitiveTraitUpdateService

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
    Score the user's assessment responses using hybrid CDM-BKT-NLP, 
    update cognitive traits, and mark onboarding complete.
    
    PHASE 1 ENHANCEMENT: Now uses same research-grade trait update 
    methodology as ongoing quiz assessments for consistency.
    """
    logger.info(f"📥 [ONBOARDING] Assessment submission from {current_user.id} ({current_user.email})")
    logger.info(f"📊 Number of responses: {len(submission.responses)}")
    
    # Initialize trait update service (hybrid CDM-BKT-NLP)
    trait_service = CognitiveTraitUpdateService()
    
    # Convert assessment responses to format expected by trait update service
    # Format: same as quiz responses (question_number, selected_answer, confidence, reasoning)
    questions = get_assessment_questions()
    question_map = {q.id: q for q in questions}
    
    formatted_responses = []
    mock_questions = []
    
    for i, resp in enumerate(submission.responses):
        question = question_map.get(resp.question_id)
        if not question:
            logger.warning(f"⚠️ Question {resp.question_id} not found in assessment bank")
            continue
        
        # Create mock question structure for trait update service
        mock_questions.append({
            "question_number": i + 1,
            "stem": question.text,
            "difficulty": question.difficulty,
            "options": [
                {"text": "User's reasoning-based answer", "type": "user_response"}
            ]
        })
        
        # Format response
        formatted_responses.append({
            "question_number": i + 1,
            "selected_answer": "User's reasoning-based answer",
            "is_correct": True,  # Onboarding focuses on reasoning quality, not correctness
            "confidence": resp.confidence if resp.confidence is not None else 0.7,
            "reasoning": resp.answer_text
        })
    
    logger.info(f"📝 Formatted {len(formatted_responses)} responses for hybrid trait analysis")
    
    # Get current traits (baseline 0.5 for new users)
    current_traits = current_user.cognitive_traits.model_dump() if current_user.cognitive_traits else {
        "precision": 0.5,
        "confidence": 0.5,
        "analytical_depth": 0.5,
        "curiosity": 0.5,
        "metacognition": 0.5,
        "cognitive_flexibility": 0.5,
        "pattern_recognition": 0.5,
        "attention_consistency": 0.5
    }
    
    # Apply hybrid CDM-BKT-NLP trait update (PHASE 1 ENHANCEMENT)
    logger.info("🧠 Applying hybrid CDM-BKT-NLP trait analysis for onboarding...")
    try:
        trait_update_result = await trait_service.update_traits(
            responses=formatted_responses,
            questions=mock_questions,
            current_traits=current_traits,
            misconceptions=[],  # No misconception targeting in onboarding
            topic_name="Onboarding Diagnostic Assessment"  # PHASE 1: Topic tracking
        )
        
        scored_traits = trait_update_result.get("updated_traits", current_traits)
        logger.info(f"✅ Hybrid trait analysis complete: {scored_traits}")
        
        # Log evidence for research analysis (PHASE 1: Evidence logging)
        evidence_log = trait_update_result.get("evidence_log", [])
        if evidence_log:
            logger.info(f"📋 Evidence log: {len(evidence_log)} entries collected")
    
    except Exception as e:
        logger.error(f"❌ Hybrid trait analysis failed: {e}", exc_info=True)
        logger.info("⚠️ Falling back to baseline traits (0.5)")
        scored_traits = current_traits
    
    # Update user record with new traits and mark onboarding complete
    await collection.update_one(
        {"_id": current_user.id},
        {
            "$set": {
                "cognitive_traits": scored_traits,
                "onboarding_completed": True,
                # PHASE 1: Store onboarding as first topic-level assessment
                f"topic_traits.Onboarding Diagnostic Assessment": {
                    "topic_name": "Onboarding Diagnostic Assessment",
                    "traits": scored_traits,
                    "question_count": len(formatted_responses),
                    "last_updated": datetime.utcnow()
                }
            }
        },
    )
    
    logger.info(f"💾 Updated {current_user.id} with hybrid-scored traits, onboarding_completed=True")
    logger.info(f"🎯 PHASE 1 COMPLETE: Onboarding now uses research-grade CDM-BKT-NLP!")

    updated_doc = await collection.find_one({"_id": current_user.id})
    if not updated_doc:
        raise HTTPException(status_code=404, detail="User not found after update")

    logger.info(f"✅ Onboarding assessment complete for {current_user.email}")
    return UserModel(**updated_doc)

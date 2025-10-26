"""Response domain models for answer submission and trait feedback."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user_model import CognitiveTraits


class ResponseSubmission(BaseModel):
    """Payload submitted when a learner answers a generated question."""

    user_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    selected_option: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str | None = None


class TraitSummary(BaseModel):
    """Snapshot of the learner's updated cognitive traits."""

    user_id: str = Field(min_length=1)
    traits: CognitiveTraits
    updated_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = ["ResponseSubmission", "TraitSummary"]

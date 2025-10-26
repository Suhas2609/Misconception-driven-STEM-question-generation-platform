"""User domain models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CognitiveTraits(BaseModel):
    """Represents a learner's cognitive signature."""

    precision: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    analytical_depth: float = Field(default=0.5, ge=0.0, le=1.0)
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0)
    metacognition: float = Field(default=0.5, ge=0.0, le=1.0)
    cognitive_flexibility: float = Field(default=0.5, ge=0.0, le=1.0)
    pattern_recognition: float = Field(default=0.5, ge=0.0, le=1.0)
    attention_consistency: float = Field(default=0.5, ge=0.0, le=1.0)


class UserModel(BaseModel):
    """Primary user record stored in MongoDB."""

    id: str | None = Field(default=None)
    name: str = Field(min_length=1)
    email: EmailStr
    password_hash: str | None = Field(default=None, exclude=True)
    cognitive_traits: CognitiveTraits = Field(default_factory=CognitiveTraits)
    onboarding_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = ["CognitiveTraits", "UserModel"]

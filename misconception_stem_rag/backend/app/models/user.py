"""User domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, EmailStr, Field

from .misconception import PersonalMisconception


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


class TopicTraitProfile(BaseModel):
    """Per-topic cognitive trait profile for domain-specific tracking."""
    
    topic_name: str = Field(description="Topic/domain name (e.g., 'Java Exception Handling')")
    traits: CognitiveTraits = Field(default_factory=CognitiveTraits)
    question_count: int = Field(default=0, description="Number of questions answered in this topic")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic_name": "Kinematics and Motion",
                "traits": {
                    "precision": 0.72,
                    "analytical_depth": 0.65
                },
                "question_count": 5,
                "last_updated": "2025-10-29T12:30:00Z"
            }
        }


class UserModel(BaseModel):
    """Primary user record stored in MongoDB."""

    id: str | None = Field(default=None)
    name: str = Field(min_length=1)
    email: EmailStr
    password_hash: str | None = Field(default=None, exclude=True)
    cognitive_traits: CognitiveTraits = Field(default_factory=CognitiveTraits)
    topic_traits: dict[str, TopicTraitProfile] = Field(
        default_factory=dict,
        description="Per-topic trait profiles for domain-specific tracking"
    )
    personal_misconceptions: Dict[str, List[PersonalMisconception]] = Field(
        default_factory=dict,
        description="Per-topic personal misconceptions discovered from quiz responses. Key: topic name, Value: list of misconceptions"
    )
    onboarding_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


__all__ = ["CognitiveTraits", "TopicTraitProfile", "UserModel"]

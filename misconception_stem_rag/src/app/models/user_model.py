"""User domain models.

Example
-------
>>> sample = {
...     "id": "user_123",
...     "name": "Ada Lovelace",
...     "email": "ada@example.com",
...     "cognitive_traits": {"precision": 0.7, "confidence": 0.6, "analytical_depth": 0.9},
... }
>>> UserModel.model_validate(sample).name
'Ada Lovelace'
"""

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


# Validate module-level sample to guarantee schema correctness on import.
_SAMPLE_USER = UserModel.model_validate(
    {
        "id": "sample_user",
        "name": "Grace Hopper",
        "email": "grace.hopper@example.com",
        "cognitive_traits": {
            "precision": 0.8,
            "confidence": 0.75,
            "analytical_depth": 0.85,
        },
    }
)

__all__ = ["CognitiveTraits", "UserModel"]

"""Question domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    """Single multiple-choice option."""

    text: str = Field(min_length=1)
    type: str = Field(pattern=r"^(correct|misconception|partial|procedural)$")


class QuestionModel(BaseModel):
    """Persisted question generated for a user."""

    id: str | None = Field(default=None)
    topic: str = Field(min_length=1)
    stem: str = Field(min_length=1)
    options: list[dict[str, str]] = Field(default_factory=list)
    explanation: str = Field(min_length=1)
    difficulty: str = Field(pattern=r"^(easy|medium|hard)$")
    user_id: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context: Any) -> None:  # noqa: D401 - pydantic hook
        """Coerce dict options into validated QuestionOption instances."""

        self.options = [QuestionOption.model_validate(opt).model_dump() for opt in self.options]


class QuestionResponse(QuestionModel):
    """Alias for API responses."""


class QuestionRequest(BaseModel):
    """Incoming payload to generate a new question."""

    user_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    factual_context: str | None = None
    misconceptions: list[str] = Field(default_factory=list)
    traits: dict[str, Any] | None = None


__all__ = [
    "QuestionModel",
    "QuestionOption",
    "QuestionRequest",
    "QuestionResponse",
]

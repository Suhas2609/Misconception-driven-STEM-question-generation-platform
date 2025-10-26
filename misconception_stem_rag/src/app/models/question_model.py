"""Question domain models.

Example
-------
>>> payload = {
...     "id": "q-001",
...     "topic": "kinematics",
...     "stem": "What is the acceleration due to gravity near Earth's surface?",
...     "options": [
...         {"text": "About 9.8 m/s^2 downward", "type": "correct"},
...         {"text": "About 9.8 m/s upward", "type": "misconception"},
...         {"text": "Zero when stationary", "type": "procedural"},
...         {"text": "Depends on mass", "type": "partial"},
...     ],
...     "explanation": "Gravity accelerates objects downward at ~9.8 m/s^2.",
...     "difficulty": "easy",
...     "user_id": "sample_user",
... }
>>> QuestionModel.model_validate(payload).topic
'kinematics'
"""

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


# Validate module-level sample to guarantee schema correctness on import.
_SAMPLE_QUESTION = QuestionModel.model_validate(
    {
        "id": "sample_q",
        "topic": "thermodynamics",
        "stem": "What does the second law of thermodynamics imply?",
        "options": [
            {"text": "Entropy of an isolated system never decreases", "type": "correct"},
            {"text": "Energy is created from nothing", "type": "misconception"},
            {"text": "Entropy stays perfectly constant", "type": "procedural"},
            {"text": "Entropy of open systems must decrease", "type": "partial"},
        ],
        "explanation": "The second law states entropy of isolated systems does not decrease.",
        "difficulty": "medium",
        "user_id": "sample_user",
        "timestamp": datetime.utcnow().isoformat(),
    }
)

class QuestionResponse(QuestionModel):
    """Alias for API responses."""


class QuestionRequest(BaseModel):
    """Incoming payload to generate a new question."""

    user_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    factual_context: str | None = None
    misconceptions: list[str] = Field(default_factory=list)
    traits: dict[str, Any] | None = None


__all__ = ["QuestionModel", "QuestionOption", "QuestionRequest", "QuestionResponse"]

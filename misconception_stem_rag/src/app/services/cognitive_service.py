"""Cognitive trait helper utilities."""

from __future__ import annotations

from collections.abc import Mapping

from app.database import mongo
from app.models.user_model import CognitiveTraits

BASELINE_TRAITS = CognitiveTraits(
    precision=0.5,
    confidence=0.5,
    analytical_depth=0.5,
    curiosity=0.5,
    metacognition=0.5,
    cognitive_flexibility=0.5,
    pattern_recognition=0.5,
    attention_consistency=0.5,
)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def init_profile() -> CognitiveTraits:
    """Return a fresh cognitive trait profile with baseline values."""

    return CognitiveTraits(**BASELINE_TRAITS.model_dump())


def derive_traits(overrides: Mapping[str, float] | None = None) -> CognitiveTraits:
    base = BASELINE_TRAITS.model_dump()
    if overrides:
        for key, value in overrides.items():
            if key in base:
                base[key] = _clamp(float(value))
    return CognitiveTraits(**base)


async def update_traits(user_id: str, quiz_feedback: Mapping[str, float]) -> CognitiveTraits:
    """Blend stored traits with feedback via simple averaging and persist the result."""

    collection = mongo.get_collection("users")
    user_doc = await collection.find_one({"_id": user_id}) or await collection.find_one(
        {"email": user_id}
    )
    if not user_doc:
        raise ValueError("User not found when updating traits")

    current = CognitiveTraits(**user_doc.get("cognitive_traits", BASELINE_TRAITS.model_dump()))
    updated_map = current.model_dump()
    for key, feedback_value in quiz_feedback.items():
        if key in updated_map:
            updated_map[key] = _clamp((updated_map[key] + float(feedback_value)) / 2)

    await collection.update_one(
        {"_id": user_doc.get("_id", user_id)},
        {"$set": {"cognitive_traits": updated_map}},
    )
    return CognitiveTraits(**updated_map)

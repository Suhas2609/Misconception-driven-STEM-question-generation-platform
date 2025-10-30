"""
PHASE 3: Difficulty Calibration System

This service maps cognitive trait scores to appropriate difficulty levels
and tracks effectiveness over time for research analysis.
"""

from __future__ import annotations

import logging
from typing import Literal
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

DifficultyLevel = Literal["easy", "medium", "hard", "expert"]


class DifficultyRecommendation(BaseModel):
    """Recommended difficulty levels for a user's cognitive profile."""
    
    overall_difficulty: DifficultyLevel
    trait_specific_difficulties: dict[str, DifficultyLevel]
    reasoning: str
    confidence_score: float  # 0-1, how confident we are in this recommendation
    weak_traits: list[str] = []  # List of weak trait names
    strong_traits: list[str] = []  # List of strong trait names


class DifficultyHistory(BaseModel):
    """Track difficulty effectiveness over time."""
    
    trait_name: str
    quiz_date: datetime
    difficulty_used: DifficultyLevel
    score_before: float
    score_after: float
    score_change: float
    questions_count: int
    effectiveness: str  # "improved", "maintained", "declined"


def calibrate_difficulty_for_profile(
    cognitive_traits: dict[str, float],
    topic_name: str | None = None,
    previous_performance: dict[str, list[DifficultyHistory]] | None = None
) -> DifficultyRecommendation:
    """
    Determine optimal difficulty levels based on cognitive profile.
    
    PHASE 3 CORE LOGIC: Maps trait scores to difficulty levels using
    research-backed thresholds and adaptive adjustment.
    
    Args:
        cognitive_traits: Current trait scores (0.0-1.0)
        topic_name: Optional topic for domain-specific calibration
        previous_performance: Historical difficulty effectiveness data
    
    Returns:
        DifficultyRecommendation with overall and trait-specific levels
    """
    logger.info(f"🎯 [PHASE 3] Calibrating difficulty for cognitive profile")
    if topic_name:
        logger.info(f"   📚 Topic: {topic_name}")
    
    # Calculate overall cognitive level (average of all traits)
    trait_scores = list(cognitive_traits.values())
    avg_score = sum(trait_scores) / len(trait_scores) if trait_scores else 0.5
    
    logger.info(f"   📊 Average trait score: {avg_score:.2f}")
    
    # PHASE 3: Map average score to base difficulty level
    # Research-based thresholds (Zone of Proximal Development)
    if avg_score < 0.50:
        base_difficulty = "easy"
        reasoning_base = "Below baseline - use scaffolded questions to build confidence"
    elif avg_score < 0.65:
        base_difficulty = "medium"
        reasoning_base = "Developing skills - moderate challenge with some support"
    elif avg_score < 0.80:
        base_difficulty = "hard"
        reasoning_base = "Competent level - challenging questions to deepen mastery"
    else:
        base_difficulty = "expert"
        reasoning_base = "Advanced mastery - expert-level questions for excellence"
    
    logger.info(f"   🎓 Base difficulty: {base_difficulty}")
    
    # PHASE 3: Trait-specific difficulty mapping
    trait_difficulties = {}
    
    for trait, score in cognitive_traits.items():
        # Map individual trait scores to difficulty
        if score < 0.55:
            trait_difficulties[trait] = "easy"
        elif score < 0.70:
            trait_difficulties[trait] = "medium"
        elif score < 0.85:
            trait_difficulties[trait] = "hard"
        else:
            trait_difficulties[trait] = "expert"
    
    # PHASE 3: Adaptive adjustment based on previous performance
    if previous_performance:
        logger.info("   📈 Analyzing previous performance for adaptive adjustment...")
        adjustments = _analyze_difficulty_effectiveness(
            previous_performance,
            cognitive_traits,
            base_difficulty
        )
        
        if adjustments["should_adjust"]:
            base_difficulty = adjustments["new_difficulty"]
            reasoning_base = f"{reasoning_base}. Adjusted based on previous performance: {adjustments['reason']}"
            logger.info(f"   🔄 Adjusted difficulty to: {base_difficulty} ({adjustments['reason']})")
    
    # Calculate confidence in recommendation
    # High variance in trait scores → lower confidence
    variance = sum((s - avg_score) ** 2 for s in trait_scores) / len(trait_scores)
    confidence = max(0.5, 1.0 - variance * 2)  # Higher variance = lower confidence
    
    # Identify weak and strong traits for metadata
    weak_trait_names = [trait for trait, score in cognitive_traits.items() if score < 0.60]
    strong_trait_names = [trait for trait, score in cognitive_traits.items() if score >= 0.75]
    
    logger.info(f"   ✅ Difficulty calibration complete (confidence: {confidence:.2f})")
    
    return DifficultyRecommendation(
        overall_difficulty=base_difficulty,
        trait_specific_difficulties=trait_difficulties,
        reasoning=reasoning_base,
        confidence_score=confidence,
        weak_traits=weak_trait_names,
        strong_traits=strong_trait_names
    )


def _analyze_difficulty_effectiveness(
    history: dict[str, list[DifficultyHistory]],
    current_traits: dict[str, float],
    current_difficulty: DifficultyLevel
) -> dict:
    """
    Analyze historical difficulty effectiveness and recommend adjustments.
    
    PHASE 3 ADAPTIVE LOGIC: Learn from past performance to optimize difficulty.
    """
    adjustments = {
        "should_adjust": False,
        "new_difficulty": current_difficulty,
        "reason": "No adjustment needed"
    }
    
    # Count recent improvements vs declines
    recent_improvements = 0
    recent_declines = 0
    
    for trait, trait_history in history.items():
        # Look at last 3 quizzes for this trait
        recent = sorted(trait_history, key=lambda x: x.quiz_date, reverse=True)[:3]
        
        for entry in recent:
            if entry.effectiveness == "improved":
                recent_improvements += 1
            elif entry.effectiveness == "declined":
                recent_declines += 1
    
    # Decision logic
    if recent_declines > recent_improvements * 2:
        # Too many declines → reduce difficulty
        difficulty_order = ["easy", "medium", "hard", "expert"]
        current_idx = difficulty_order.index(current_difficulty)
        if current_idx > 0:
            adjustments["should_adjust"] = True
            adjustments["new_difficulty"] = difficulty_order[current_idx - 1]
            adjustments["reason"] = "Recent performance declined, reducing difficulty"
    
    elif recent_improvements > recent_declines * 2 and all(
        score > 0.75 for score in current_traits.values()
    ):
        # Consistent improvement + high scores → increase difficulty
        difficulty_order = ["easy", "medium", "hard", "expert"]
        current_idx = difficulty_order.index(current_difficulty)
        if current_idx < len(difficulty_order) - 1:
            adjustments["should_adjust"] = True
            adjustments["new_difficulty"] = difficulty_order[current_idx + 1]
            adjustments["reason"] = "Consistent improvement, increasing challenge"
    
    return adjustments


def get_difficulty_distribution(
    overall_difficulty: DifficultyLevel,
    trait_difficulties: dict[str, DifficultyLevel],
    weak_traits: list[tuple[str, float]],
    total_questions: int = 10
) -> dict[DifficultyLevel, int]:
    """
    Determine how many questions of each difficulty to generate.
    
    PHASE 3 ENHANCEMENT: Combines overall difficulty with trait-specific needs.
    
    Args:
        overall_difficulty: Base difficulty level
        trait_difficulties: Difficulty for each trait
        weak_traits: List of (trait_name, score) for weak traits
        total_questions: Total questions to generate
    
    Returns:
        Distribution of questions across difficulty levels
    """
    logger.info(f"📊 [PHASE 3] Determining difficulty distribution for {total_questions} questions")
    
    # Start with base distribution
    difficulty_counts = {
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "expert": 0
    }
    
    # Allocate based on overall difficulty
    if overall_difficulty == "easy":
        difficulty_counts["easy"] = int(total_questions * 0.7)
        difficulty_counts["medium"] = int(total_questions * 0.3)
    elif overall_difficulty == "medium":
        difficulty_counts["easy"] = int(total_questions * 0.2)
        difficulty_counts["medium"] = int(total_questions * 0.6)
        difficulty_counts["hard"] = int(total_questions * 0.2)
    elif overall_difficulty == "hard":
        difficulty_counts["medium"] = int(total_questions * 0.3)
        difficulty_counts["hard"] = int(total_questions * 0.6)
        difficulty_counts["expert"] = int(total_questions * 0.1)
    else:  # expert
        difficulty_counts["hard"] = int(total_questions * 0.4)
        difficulty_counts["expert"] = int(total_questions * 0.6)
    
    # Adjust for weak traits (use easier difficulties)
    if weak_traits:
        weak_count = min(3, len(weak_traits))
        # Shift some questions to easier difficulties for weak traits
        if difficulty_counts["hard"] > 0:
            shift = min(weak_count, difficulty_counts["hard"])
            difficulty_counts["hard"] -= shift
            difficulty_counts["medium"] += shift
    
    # Ensure total adds up
    actual_total = sum(difficulty_counts.values())
    if actual_total < total_questions:
        # Add remaining to most common difficulty
        difficulty_counts[overall_difficulty] += (total_questions - actual_total)
    
    logger.info(f"   Distribution: {difficulty_counts}")
    
    return difficulty_counts


def record_difficulty_effectiveness(
    trait_name: str,
    difficulty_used: DifficultyLevel,
    score_before: float,
    score_after: float,
    questions_count: int
) -> DifficultyHistory:
    """
    Record how effective a difficulty level was for a specific trait.
    
    PHASE 3 RESEARCH DATA: This enables analysis of optimal difficulty per trait.
    """
    score_change = score_after - score_before
    
    # Determine effectiveness
    if score_change > 0.02:
        effectiveness = "improved"
    elif score_change < -0.02:
        effectiveness = "declined"
    else:
        effectiveness = "maintained"
    
    history_entry = DifficultyHistory(
        trait_name=trait_name,
        quiz_date=datetime.utcnow(),
        difficulty_used=difficulty_used,
        score_before=score_before,
        score_after=score_after,
        score_change=score_change,
        questions_count=questions_count,
        effectiveness=effectiveness
    )
    
    logger.info(
        f"📝 [PHASE 3] Recorded difficulty effectiveness: "
        f"{trait_name} @ {difficulty_used} → {effectiveness} ({score_change:+.3f})"
    )
    
    return history_entry


def get_difficulty_guidance_for_prompt(
    difficulty: DifficultyLevel,
    trait_name: str | None = None
) -> str:
    """
    Generate specific guidance for GPT-4o on how to create questions at this difficulty.
    
    PHASE 3 PROMPT ENHANCEMENT: Explicit difficulty instructions.
    """
    difficulty_guidelines = {
        "easy": {
            "general": "Create straightforward questions with clear, direct language. Provide scaffolding and hints. Focus on fundamental concepts with minimal complexity.",
            "precision": "Simple calculations with clear steps. Provide formulas and unit hints.",
            "analytical_depth": "Break problems into obvious sub-steps. Use clear cause-effect relationships.",
            "metacognition": "Include explicit reflection prompts. Ask direct 'why' questions.",
            "curiosity": "Present accessible 'what if' scenarios with guided exploration."
        },
        "medium": {
            "general": "Create moderately challenging questions requiring some independent thinking. Balance support with challenge.",
            "precision": "Multi-step calculations requiring careful attention. Some formula recall needed.",
            "analytical_depth": "Problems requiring 2-3 analytical steps. Some synthesis needed.",
            "metacognition": "Require strategy comparison. Ask about thought processes.",
            "curiosity": "Open-ended exploration with moderate guidance."
        },
        "hard": {
            "general": "Create challenging questions requiring deep understanding. Minimal scaffolding. Expect independent reasoning.",
            "precision": "Complex calculations with multiple conversions. High precision required.",
            "analytical_depth": "Multi-layered problems requiring systematic decomposition.",
            "metacognition": "Meta-level analysis of strategies and error patterns.",
            "curiosity": "Abstract hypotheticals requiring creative exploration."
        },
        "expert": {
            "general": "Create expert-level questions for mastery demonstration. No scaffolding. Expect sophisticated reasoning.",
            "precision": "Highly complex calculations with edge cases and error analysis.",
            "analytical_depth": "System-level analysis requiring advanced synthesis.",
            "metacognition": "Deep reflection on cognitive strategies and meta-patterns.",
            "curiosity": "Novel scenarios requiring paradigm shifts and innovation."
        }
    }
    
    guidelines = difficulty_guidelines.get(difficulty, difficulty_guidelines["medium"])
    
    if trait_name and trait_name in guidelines:
        return guidelines[trait_name]
    else:
        return guidelines["general"]

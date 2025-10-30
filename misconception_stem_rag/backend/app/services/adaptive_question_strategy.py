"""
PHASE 2: Adaptive Question Generation Strategy

This service analyzes cognitive profiles and determines optimal question 
generation strategies to target weaknesses and reinforce strengths.
"""

from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WeaknessAnalysis(BaseModel):
    """Analysis of cognitive weaknesses and recommended question targeting."""
    
    weak_traits: list[tuple[str, float]]  # [(trait_name, score), ...]
    moderate_traits: list[tuple[str, float]]
    strong_traits: list[tuple[str, float]]
    
    # Question distribution recommendations
    questions_for_weak_traits: int
    questions_for_moderate_traits: int
    questions_for_strong_traits: int
    
    # Explicit targeting instructions for prompt
    targeting_strategy: str


def analyze_cognitive_profile(
    cognitive_traits: dict[str, float],
    total_questions: int = 10,
    topic_name: str | None = None
) -> WeaknessAnalysis:
    """
    Analyze cognitive profile and create adaptive question generation strategy.
    
    PHASE 2 ENHANCEMENT: This enables explicit weakness targeting instead of
    relying on GPT-4o to implicitly adjust based on trait scores.
    
    Args:
        cognitive_traits: User's current trait scores (0.0-1.0)
        total_questions: Total number of questions to generate
        topic_name: Optional topic name for topic-specific analysis
    
    Returns:
        WeaknessAnalysis with detailed targeting strategy
    """
    logger.info(f"🎯 [PHASE 2] Analyzing cognitive profile for adaptive question generation")
    if topic_name:
        logger.info(f"   📚 Topic context: {topic_name}")
    
    # Categorize traits by strength level
    weak_traits = []      # < 60%
    moderate_traits = []  # 60-80%
    strong_traits = []    # > 80%
    
    for trait, score in cognitive_traits.items():
        percentage = score * 100 if isinstance(score, float) else score
        
        if percentage < 60:
            weak_traits.append((trait, score))
        elif percentage < 80:
            moderate_traits.append((trait, score))
        else:
            strong_traits.append((trait, score))
    
    # Sort each category by score (weakest first, strongest last)
    weak_traits.sort(key=lambda x: x[1])
    moderate_traits.sort(key=lambda x: x[1])
    strong_traits.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(f"   📉 Weak traits (< 60%): {len(weak_traits)}")
    logger.info(f"   📊 Moderate traits (60-80%): {len(moderate_traits)}")
    logger.info(f"   📈 Strong traits (> 80%): {len(strong_traits)}")
    
    # Determine question distribution (adaptive weighting)
    # Priority: Focus on weaknesses, maintain strengths, challenge moderates
    if weak_traits:
        # If weaknesses exist, allocate 60% of questions to them
        questions_for_weak = max(1, int(total_questions * 0.6))
        questions_for_moderate = max(1, int(total_questions * 0.25))
        questions_for_strong = total_questions - questions_for_weak - questions_for_moderate
    elif moderate_traits:
        # No weaknesses but moderates exist - focus there
        questions_for_weak = 0
        questions_for_moderate = max(1, int(total_questions * 0.7))
        questions_for_strong = total_questions - questions_for_moderate
    else:
        # All traits strong - maintain with challenging questions
        questions_for_weak = 0
        questions_for_moderate = 0
        questions_for_strong = total_questions
    
    logger.info(f"   📋 Question distribution: {questions_for_weak} weak, {questions_for_moderate} moderate, {questions_for_strong} strong")
    
    # Build explicit targeting strategy for GPT-4o prompt
    targeting_parts = []
    
    if weak_traits:
        weak_names = [f"{name} ({score*100:.0f}%)" for name, score in weak_traits[:3]]
        targeting_parts.append(
            f"**PRIMARY FOCUS (60% of questions):** Target these WEAK traits: {', '.join(weak_names)}. "
            f"Generate {questions_for_weak} questions that require and develop these skills."
        )
    
    if moderate_traits:
        moderate_names = [f"{name} ({score*100:.0f}%)" for name, score in moderate_traits[:2]]
        targeting_parts.append(
            f"**SECONDARY FOCUS (25% of questions):** Challenge these DEVELOPING traits: {', '.join(moderate_names)}. "
            f"Generate {questions_for_moderate} questions at moderate-to-high difficulty."
        )
    
    if strong_traits:
        strong_names = [f"{name} ({score*100:.0f}%)" for name, score in strong_traits[:2]]
        targeting_parts.append(
            f"**MAINTENANCE (15% of questions):** Reinforce these STRONG traits: {', '.join(strong_names)}. "
            f"Generate {questions_for_strong} challenging questions to maintain mastery."
        )
    
    targeting_strategy = "\n".join(targeting_parts)
    
    logger.info(f"✅ [PHASE 2] Adaptive strategy created")
    
    return WeaknessAnalysis(
        weak_traits=weak_traits,
        moderate_traits=moderate_traits,
        strong_traits=strong_traits,
        questions_for_weak_traits=questions_for_weak,
        questions_for_moderate_traits=questions_for_moderate,
        questions_for_strong_traits=questions_for_strong,
        targeting_strategy=targeting_strategy
    )


def get_trait_specific_instructions(trait_name: str, score: float) -> str:
    """
    Get specific instructions for generating questions that target a particular trait.
    
    PHASE 2 ENHANCEMENT: Provides explicit guidance to GPT-4o on how to create
    questions that challenge specific cognitive traits.
    
    Args:
        trait_name: Name of the cognitive trait
        score: Current score (0.0-1.0)
    
    Returns:
        Detailed instructions for question design
    """
    trait_instructions = {
        "precision": {
            "focus": "numerical accuracy, unit conversions, significant figures, exact calculations",
            "question_types": "multi-step calculations, unit analysis, precision-dependent scenarios"
        },
        "confidence": {
            "focus": "calibration between stated confidence and correctness",
            "question_types": "questions with tempting but incorrect options, require explicit confidence rating"
        },
        "analytical_depth": {
            "focus": "breaking down complex problems, identifying sub-problems, systematic analysis",
            "question_types": "multi-layered problems, cause-effect chains, system decomposition"
        },
        "curiosity": {
            "focus": "exploring edge cases, asking 'what if', going beyond surface understanding",
            "question_types": "open-ended exploration, hypothetical scenarios, variant testing"
        },
        "metacognition": {
            "focus": "awareness of thought processes, strategy reflection, error recognition",
            "question_types": "strategy comparison, error analysis, self-assessment prompts"
        },
        "cognitive_flexibility": {
            "focus": "adapting to new information, handling contradictions, abstract thinking",
            "question_types": "contradictory premises, paradigm shifts, abstract/hypothetical scenarios"
        },
        "pattern_recognition": {
            "focus": "identifying rules, sequences, structural regularities, analogies",
            "question_types": "pattern completion, rule identification, structural analogies"
        },
        "attention_consistency": {
            "focus": "sustained focus, multi-step tracking, avoiding impulsive errors",
            "question_types": "multi-step problems, detail-heavy scenarios, sequential reasoning"
        }
    }
    
    instructions = trait_instructions.get(trait_name, {
        "focus": "general cognitive skills",
        "question_types": "varied problem types"
    })
    
    # Adjust difficulty based on score
    if score < 0.6:
        difficulty_guidance = "Use SCAFFOLDED questions (provide hints, break into smaller steps)"
    elif score < 0.8:
        difficulty_guidance = "Use MODERATE difficulty (some guidance, but require independent thinking)"
    else:
        difficulty_guidance = "Use CHALLENGING questions (minimal hints, expect expert-level reasoning)"
    
    return (
        f"For {trait_name} (current score: {score*100:.0f}%): "
        f"Focus on {instructions['focus']}. "
        f"{difficulty_guidance}. "
        f"Question types: {instructions['question_types']}."
    )

"""Cognitive assessment question bank and models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssessmentQuestion(BaseModel):
    """Single cognitive assessment question."""

    id: str
    text: str = Field(description="The question prompt")
    context: str | None = Field(default=None, description="Optional scenario/context")
    traits_targeted: list[str] = Field(
        default_factory=list,
        description="Which cognitive traits this question probes",
    )
    difficulty: str = Field(default="medium", description="easy | medium | hard")
    category: str = Field(
        default="reasoning",
        description="reasoning | estimation | pattern | abstract | metacognitive",
    )


# Seed assessment questions for onboarding
ASSESSMENT_QUESTIONS: list[AssessmentQuestion] = [
    AssessmentQuestion(
        id="assess_01",
        text="A standard city bus is approximately 12 meters long, 2.5 meters wide, and 3 meters tall. Estimate the interior volume available for passengers in cubic meters, accounting for driver cabin, engine compartment, and seating structures.",
        context="Fermi estimation problem requiring spatial reasoning and practical constraints.",
        traits_targeted=["analytical_depth", "precision", "pattern_recognition"],
        difficulty="medium",
        category="estimation",
    ),
    AssessmentQuestion(
        id="assess_02",
        text="You discover your solution to a complex problem was incorrect. Describe your thought process: how would you identify where your reasoning failed and what steps would you take to correct it?",
        context="Meta-cognitive reflection on error analysis.",
        traits_targeted=["metacognition", "cognitive_flexibility", "curiosity"],
        difficulty="medium",
        category="metacognitive",
    ),
    AssessmentQuestion(
        id="assess_03",
        text="Given the sequence: 2, 6, 12, 20, 30, ... What is the next number and what rule generates this sequence?",
        context="Pattern recognition in numerical sequences.",
        traits_targeted=["pattern_recognition", "analytical_depth", "precision"],
        difficulty="easy",
        category="pattern",
    ),
    AssessmentQuestion(
        id="assess_04",
        text="A farmer has 100 meters of fencing and wants to enclose a rectangular area. What dimensions maximize the enclosed area? Explain your reasoning process step-by-step.",
        context="Optimization problem requiring systematic exploration.",
        traits_targeted=["analytical_depth", "precision", "metacognition"],
        difficulty="medium",
        category="reasoning",
    ),
    AssessmentQuestion(
        id="assess_05",
        text="Imagine a world where water freezes at 100°C and boils at 0°C. Describe three immediate consequences for weather patterns, biology, and human infrastructure.",
        context="Hypothetical scenario testing flexible thinking and interconnected reasoning.",
        traits_targeted=["cognitive_flexibility", "curiosity", "analytical_depth"],
        difficulty="hard",
        category="abstract",
    ),
    AssessmentQuestion(
        id="assess_06",
        text="You are given a dataset showing crime rates have increased in areas with more ice cream sales. Does ice cream cause crime? Explain what factors you would investigate and why correlation doesn't imply causation.",
        context="Critical reasoning about spurious correlations.",
        traits_targeted=["analytical_depth", "metacognition", "precision"],
        difficulty="medium",
        category="reasoning",
    ),
    AssessmentQuestion(
        id="assess_07",
        text="A clock shows 3:15. What is the angle between the hour and minute hands? Show your calculation process.",
        context="Spatial reasoning with time-based geometry.",
        traits_targeted=["precision", "analytical_depth", "attention_consistency"],
        difficulty="easy",
        category="reasoning",
    ),
    AssessmentQuestion(
        id="assess_08",
        text="Before attempting a challenging problem, what strategies do you use to break it down? Describe your personal problem-solving framework.",
        context="Metacognitive awareness of personal strategies.",
        traits_targeted=["metacognition", "cognitive_flexibility", "curiosity"],
        difficulty="medium",
        category="metacognitive",
    ),
    AssessmentQuestion(
        id="assess_09",
        text="If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies? Explain your logical reasoning.",
        context="Abstract logical inference testing.",
        traits_targeted=["analytical_depth", "precision", "pattern_recognition"],
        difficulty="easy",
        category="abstract",
    ),
    AssessmentQuestion(
        id="assess_10",
        text="Estimate how many piano tuners are currently working in New York City. Explain each assumption you make and how you arrive at your estimate.",
        context="Classic Fermi problem requiring decomposition and estimation.",
        traits_targeted=["analytical_depth", "precision", "curiosity", "metacognition"],
        difficulty="hard",
        category="estimation",
    ),
    AssessmentQuestion(
        id="assess_11",
        text="You notice your confidence in answers tends to be higher than your actual accuracy. How would you calibrate your confidence going forward?",
        context="Confidence calibration and self-awareness.",
        traits_targeted=["metacognition", "confidence", "cognitive_flexibility"],
        difficulty="medium",
        category="metacognitive",
    ),
    AssessmentQuestion(
        id="assess_12",
        text="A bat and ball together cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost? Explain why many people get this wrong initially.",
        context="Classic cognitive reflection test item.",
        traits_targeted=["attention_consistency", "precision", "metacognition"],
        difficulty="medium",
        category="reasoning",
    ),
    AssessmentQuestion(
        id="assess_13",
        text="Observe this pattern: ○ ● ○ ○ ● ○ ○ ○ ● ... What comes next and what principle governs this sequence?",
        context="Visual pattern recognition with increasing intervals.",
        traits_targeted=["pattern_recognition", "analytical_depth", "curiosity"],
        difficulty="medium",
        category="pattern",
    ),
    AssessmentQuestion(
        id="assess_14",
        text="When you encounter a concept that contradicts your existing understanding, describe your typical reaction and how you reconcile the conflict.",
        context="Cognitive flexibility and belief updating.",
        traits_targeted=["cognitive_flexibility", "curiosity", "metacognition"],
        difficulty="medium",
        category="metacognitive",
    ),
    AssessmentQuestion(
        id="assess_15",
        text="A snail is at the bottom of a 10-meter well. Each day it climbs up 3 meters, but each night it slides down 2 meters. How many days does it take to escape the well? Show your reasoning.",
        context="Problem requiring careful tracking and avoiding premature pattern assumptions.",
        traits_targeted=["analytical_depth", "attention_consistency", "precision"],
        difficulty="medium",
        category="reasoning",
    ),
]


def get_assessment_questions() -> list[AssessmentQuestion]:
    """Return the full cognitive assessment question bank."""
    return ASSESSMENT_QUESTIONS

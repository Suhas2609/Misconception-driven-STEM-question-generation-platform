"""
GPT-4o Explanation Generation Service
This is the THIRD MAJOR PROMPT ENGINEERING task - generating personalized feedback
"""

from __future__ import annotations

import json
import logging
from typing import Any
from textwrap import dedent

from openai import OpenAI
from ..config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()
_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    """Get or create OpenAI client singleton."""
    global _client
    api_key = _settings.openai_api_key
    if not api_key or "REDACTED" in api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def generate_personalized_explanation(
    question: dict[str, Any],
    user_answer: str,
    is_correct: bool,
    confidence: float,
    reasoning: str | None,
    cognitive_traits: dict[str, float]
) -> dict[str, Any]:
    """
    Generate personalized explanation using GPT-4o based on:
    - The question and all options
    - User's selected answer
    - Whether it was correct
    - User's confidence level
    - User's reasoning (if provided)
    - User's cognitive profile
    
    Returns:
    {
        "explanation": "Detailed explanation text",
        "misconception_addressed": "If wrong, what misconception was revealed",
        "learning_tips": ["Tip 1", "Tip 2"],
        "confidence_analysis": "Analysis of confidence calibration"
    }
    """
    
    client = _get_client()
    if not client:
        return _fallback_explanation(is_correct)
    
    # Build the prompt
    prompt = _build_explanation_prompt(
        question, user_answer, is_correct, confidence, reasoning, cognitive_traits
    )
    
    try:
        response = client.chat.completions.create(
            model=_settings.openai_model or "gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert STEM tutor providing personalized feedback. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # More focused for explanations
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        if not content:
            return _fallback_explanation(is_correct)
        
        # Strip markdown fences
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        explanation_data = json.loads(content)
        
        logger.info(f"✅ Generated personalized explanation (correct={is_correct})")
        return explanation_data
        
    except Exception as e:
        logger.error(f"❌ Failed to generate explanation: {e}", exc_info=True)
        return _fallback_explanation(is_correct)


def _build_explanation_prompt(
    question: dict[str, Any],
    user_answer: str,
    is_correct: bool,
    confidence: float,
    reasoning: str | None,
    cognitive_traits: dict[str, float]
) -> str:
    """Build the GPT-4o prompt for explanation generation."""
    
    # Format cognitive traits
    trait_lines = []
    for trait, score in cognitive_traits.items():
        percentage = int(score * 100) if isinstance(score, float) else int(score)
        trait_lines.append(f"- {trait}: {percentage}%")
    traits_text = "\n".join(trait_lines) if trait_lines else "- No profile available"
    
    # Find the correct answer
    correct_option = None
    user_option_type = None
    
    for opt in question.get("options", []):
        if opt.get("text") == user_answer:
            user_option_type = opt.get("type")
        if opt.get("type") == "correct":
            correct_option = opt.get("text")
    
    # Format question options
    options_text = "\n".join([
        f"- {opt.get('text')} [{opt.get('type').upper()}]"
        for opt in question.get("options", [])
    ])
    
    confidence_pct = int(confidence * 100)
    
    prompt = dedent(f"""
    ## LEARNER RESPONSE ANALYSIS
    
    **Question**: {question.get("stem", "N/A")}
    
    **All Options**:
    {options_text}
    
    **Correct Answer**: {correct_option}
    **User's Answer**: {user_answer}
    **Answer Type**: {user_option_type or "unknown"}
    **Result**: {"✓ CORRECT" if is_correct else "✗ INCORRECT"}
    **Confidence**: {confidence_pct}%
    **User's Reasoning**: {reasoning or "Not provided"}
    
    **Learner's Cognitive Profile**:
    {traits_text}
    
    ## YOUR TASK
    
    Provide personalized feedback tailored to this learner's profile and response:
    
    1. **Explanation**: 
       - If CORRECT: Reinforce understanding, explain why it's right, and connect to broader concepts
       - If INCORRECT: Explain the misconception, why their answer is wrong, and guide toward correct understanding
       - Keep it encouraging and constructive
       - Adapt language complexity to their analytical_reasoning score
    
    2. **Misconception Analysis** (if incorrect):
       - What specific misconception led to this error?
       - Based on the option type ({user_option_type}), explain the cognitive error
       - "misconception" type = conceptual misunderstanding
       - "partial" type = incomplete understanding
       - "procedural" type = correct process, wrong application
    
    3. **Confidence Analysis**:
       - Was their confidence calibrated correctly?
       - If overconfident (high confidence but wrong): Suggest more careful analysis
       - If underconfident (low confidence but right): Boost confidence in their reasoning
       - If well-calibrated: Reinforce their metacognitive awareness
    
    4. **Learning Tips** (2-3 actionable tips):
       - Based on their cognitive profile, suggest specific study strategies
       - If pattern_recognition is low and they missed patterns: Suggest pattern practice
       - If fermi_estimation is low and question involved estimation: Suggest estimation practice
       - Be specific and actionable
    
    ## OUTPUT FORMAT (JSON ONLY - NO MARKDOWN)
    {{
      "explanation": "Your detailed, personalized explanation here (2-3 sentences)",
      "misconception_addressed": "Specific misconception if wrong, or null if correct",
      "confidence_analysis": "Analysis of their confidence calibration (1 sentence)",
      "learning_tips": [
        "Specific actionable tip 1",
        "Specific actionable tip 2"
      ],
      "encouragement": "Personalized encouraging message (1 sentence)"
    }}
    
    Return ONLY the JSON. No markdown fences.
    """)
    
    return prompt


def _fallback_explanation(is_correct: bool) -> dict[str, Any]:
    """Fallback explanation if GPT-4o fails."""
    if is_correct:
        return {
            "explanation": "Great job! Your answer is correct. You've demonstrated solid understanding of this concept.",
            "misconception_addressed": None,
            "confidence_analysis": "Well done on your response.",
            "learning_tips": [
                "Continue practicing similar problems to reinforce your understanding",
                "Try explaining this concept to someone else to deepen your mastery"
            ],
            "encouragement": "Keep up the excellent work!"
        }
    else:
        return {
            "explanation": "This answer isn't quite right. Review the core concepts and try to identify where your reasoning diverged from the correct approach.",
            "misconception_addressed": "There may be a gap in understanding the fundamental principles of this topic.",
            "confidence_analysis": "Take time to review your reasoning process.",
            "learning_tips": [
                "Revisit the relevant textbook section or reference material",
                "Practice similar problems and check your work carefully"
            ],
            "encouragement": "Mistakes are valuable learning opportunities - keep practicing!"
        }

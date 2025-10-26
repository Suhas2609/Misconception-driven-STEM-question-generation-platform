"""Assessment scoring service using LLM to derive cognitive traits."""

from __future__ import annotations

import json
from textwrap import dedent

from openai import OpenAI

from ..config import get_settings
from ..models.assessment_model import AssessmentQuestion, get_assessment_questions
from ..models.user_model import CognitiveTraits


def score_assessment_responses(responses: list[dict[str, str]]) -> CognitiveTraits:
    """
    Use GPT-4o to analyze user's free-form reasoning responses and derive cognitive trait scores.
    
    Args:
        responses: List of dicts with 'question_id', 'answer_text', optional 'confidence'
    
    Returns:
        CognitiveTraits object with updated scores for all 8 dimensions
    """
    settings = get_settings()
    if not settings.openai_api_key or "REDACTED" in settings.openai_api_key:
        # Fallback: return baseline traits if no API key
        return CognitiveTraits()

    questions = {q.id: q for q in get_assessment_questions()}
    
    # Build rich context for scoring prompt
    context_parts = []
    for resp in responses:
        q_id = resp.get("question_id", "")
        question = questions.get(q_id)
        if not question:
            continue
        
        context_parts.append(
            f"""
**Question ID:** {q_id}
**Category:** {question.category}
**Difficulty:** {question.difficulty}
**Traits Targeted:** {', '.join(question.traits_targeted)}
**Question:** {question.text}
**User's Answer/Reasoning:** {resp.get('answer_text', 'No response')}
**Confidence (if provided):** {resp.get('confidence', 'Not specified')}
"""
        )
    
    combined_context = "\n---\n".join(context_parts)
    
    prompt = dedent(
        f"""
        You are an expert psychometric analyst specializing in cognitive profiling.
        
        You will be given a learner's responses to a set of assessment questions designed to probe their cognitive traits.
        Your task is to analyze their reasoning patterns, problem-solving approaches, metacognitive awareness, 
        and overall cognitive signature across the following 8 dimensions:
        
        1. **precision** (0.0-1.0): Attention to numerical accuracy, detail, and exactness in calculations/definitions.
        2. **confidence** (0.0-1.0): Alignment between stated confidence and actual correctness; calibrated self-assessment.
        3. **analytical_depth** (0.0-1.0): Ability to break down complex problems systematically and explore multiple angles.
        4. **curiosity** (0.0-1.0): Willingness to explore edge cases, ask "what if" questions, and go beyond the minimum.
        5. **metacognition** (0.0-1.0): Self-awareness of thought processes, recognition of errors, strategy reflection.
        6. **cognitive_flexibility** (0.0-1.0): Comfort with abstract/hypothetical scenarios, adapting to contradictory information.
        7. **pattern_recognition** (0.0-1.0): Speed and accuracy in identifying rules, sequences, and structural regularities.
        8. **attention_consistency** (0.0-1.0): Sustained focus, avoiding impulsive answers, careful tracking of multi-step problems.
        
        **Assessment Responses:**
        {combined_context}
        
        **Instructions:**
        - Analyze each response for evidence of the targeted traits plus cross-cutting signals.
        - Consider quality of reasoning, depth of explanation, error awareness, and confidence calibration.
        - Assign a score (0.0-1.0) for each of the 8 traits based on aggregate evidence.
        - Be strict but fair: 0.5 is baseline/neutral, 0.7+ indicates strength, <0.4 indicates weakness.
        - Provide brief justification for each score (1-2 sentences).
        
        Return **only** valid JSON in this exact format:
        {{
          "precision": 0.0-1.0,
          "confidence": 0.0-1.0,
          "analytical_depth": 0.0-1.0,
          "curiosity": 0.0-1.0,
          "metacognition": 0.0-1.0,
          "cognitive_flexibility": 0.0-1.0,
          "pattern_recognition": 0.0-1.0,
          "attention_consistency": 0.0-1.0,
          "justifications": {{
            "precision": "...",
            "confidence": "...",
            "analytical_depth": "...",
            "curiosity": "...",
            "metacognition": "...",
            "cognitive_flexibility": "...",
            "pattern_recognition": "...",
            "attention_consistency": "..."
          }}
        }}
        """
    ).strip()
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a cognitive assessment expert. Return only valid JSON, no markdown or prose.",
            },
            {"role": "user", "content": prompt},
        ]
        
        response = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        
        content = response.choices[0].message.content
        if not content:
            return CognitiveTraits()
        
        # Parse JSON response
        parsed = json.loads(content.strip())
        
        # Extract scores, validating range
        def clamp(val: float) -> float:
            return max(0.0, min(1.0, float(val)))
        
        traits = CognitiveTraits(
            precision=clamp(parsed.get("precision", 0.5)),
            confidence=clamp(parsed.get("confidence", 0.5)),
            analytical_depth=clamp(parsed.get("analytical_depth", 0.5)),
            curiosity=clamp(parsed.get("curiosity", 0.5)),
            metacognition=clamp(parsed.get("metacognition", 0.5)),
            cognitive_flexibility=clamp(parsed.get("cognitive_flexibility", 0.5)),
            pattern_recognition=clamp(parsed.get("pattern_recognition", 0.5)),
            attention_consistency=clamp(parsed.get("attention_consistency", 0.5)),
        )
        
        return traits
    
    except Exception:
        # On any error, return baseline traits
        return CognitiveTraits()

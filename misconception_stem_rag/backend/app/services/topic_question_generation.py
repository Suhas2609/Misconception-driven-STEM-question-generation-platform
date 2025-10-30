"""
Service for generating questions from selected topics using GPT-4o.
This is the CORE PROMPT ENGINEERING for personalized question generation.

PHASE 2 ENHANCEMENT: Added adaptive question strategy based on cognitive weaknesses.
PHASE 3 ENHANCEMENT: Added difficulty calibration based on trait scores.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from textwrap import dedent

from openai import OpenAI
from ..config import get_settings
from .adaptive_question_strategy import analyze_cognitive_profile
from .difficulty_calibration import (
    calibrate_difficulty_for_profile,
    get_difficulty_guidance_for_prompt
)
from .validation import get_related_misconceptions
from .misconception_extraction import get_user_personal_misconceptions

logger = logging.getLogger(__name__)
_settings = get_settings()
_client: OpenAI | None = None


def _infer_subject_from_title(topic_title: str) -> str | None:
    """
    Infer subject area from topic title using keyword matching.
    
    Returns:
        Subject area string or None if cannot be inferred
    """
    title_lower = topic_title.lower()
    
    # Physics keywords
    if any(kw in title_lower for kw in ["force", "motion", "newton", "gravity", "energy", "momentum", "velocity", "acceleration", "physics"]):
        return "Physics"
    
    # Chemistry keywords
    if any(kw in title_lower for kw in ["bond", "molecule", "reaction", "element", "compound", "acid", "base", "chemistry", "hydrogen"]):
        return "Chemistry"
    
    # Biology keywords
    if any(kw in title_lower for kw in ["cell", "gene", "dna", "organism", "protein", "biology", "evolution", "photosynthesis"]):
        return "Biology"
    
    # Mathematics keywords
    if any(kw in title_lower for kw in ["equation", "algebra", "calculus", "geometry", "function", "derivative", "integral", "math"]):
        return "Mathematics"
    
    return None


def _get_client() -> OpenAI | None:
    """Get or create OpenAI client singleton."""
    global _client
    api_key = _settings.openai_api_key
    if not api_key or "REDACTED" in api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def build_question_generation_prompt(
    topic_title: str,
    topic_description: str,
    pdf_content: str,
    cognitive_traits: dict[str, float],
    difficulty: str = "intermediate",
    total_questions: int = 10,  # PHASE 2: Added for adaptive distribution
    personal_misconceptions: list[dict] | None = None,  # PHASE 5: Personal misconceptions
    subject_area: str | None = None  # NEW: Subject area for domain filtering
) -> str:
    """
    Build the GPT-4o prompt for generating personalized STEM questions.
    
    PHASE 2 ENHANCEMENT: Now analyzes cognitive profile and explicitly targets
    weaknesses with adaptive question distribution.
    
    PHASE 3 ENHANCEMENT: Calibrates difficulty based on trait scores (weak traits
    get easier questions, strong traits get challenging questions).
    
    PHASE 5 ENHANCEMENT: Targets student's personal misconceptions discovered from
    previous quiz responses for remedial learning.
    
    This is the MAIN PROMPT ENGINEERING task - it combines:
    - Topic from PDF extraction
    - User's cognitive profile + weakness analysis (PHASE 2)
    - Difficulty calibration based on trait strengths (PHASE 3)
    - PDF content (RAG)
    - Common misconceptions from database (PHASE 4)
    - Personal student misconceptions (PHASE 5 - NEW!)
    - Adaptive targeting strategy (PHASE 2)
    """
    
    # PHASE 2: Analyze cognitive profile for adaptive targeting
    weakness_analysis = analyze_cognitive_profile(
        cognitive_traits=cognitive_traits,
        total_questions=total_questions,
        topic_name=topic_title
    )
    
    # PHASE 3: Calibrate difficulty based on trait scores
    calibrated_difficulty = calibrate_difficulty_for_profile(cognitive_traits)
    difficulty_guidance = get_difficulty_guidance_for_prompt(calibrated_difficulty.overall_difficulty)
    
    # PHASE 4: Retrieve related misconceptions from database
    # CRITICAL: Filter by subject_area/domain to prevent cross-contamination
    topic_subject = subject_area or _infer_subject_from_title(topic_title)
    
    related_misconceptions = get_related_misconceptions(
        topic_title, 
        limit=3,
        domain=topic_subject  # Pass domain filter to prevent cross-contamination
    )
    misconception_texts = [m.get('misconception_text', '') for m in related_misconceptions if m.get('misconception_text')]
    
    logger.info(f"📊 [PHASE 2] Adaptive strategy: {weakness_analysis.questions_for_weak_traits} weak, "
                f"{weakness_analysis.questions_for_moderate_traits} moderate, "
                f"{weakness_analysis.questions_for_strong_traits} strong")
    logger.info(f"🎚️ [PHASE 3] Calibrated difficulty: {calibrated_difficulty.overall_difficulty} "
                f"(weak traits: {len(calibrated_difficulty.weak_traits)}, "
                f"strong traits: {len(calibrated_difficulty.strong_traits)})")
    logger.info(f"🧠 [PHASE 4] Retrieved {len(misconception_texts)} {topic_subject or 'general'} misconceptions from database")
    
    # Format cognitive traits for the prompt (original logic)
    trait_analysis = []
    for trait, score in cognitive_traits.items():
        percentage = int(score * 100) if isinstance(score, float) else int(score)
        trait_analysis.append(f"- {trait}: {percentage}% ({_interpret_trait(trait, percentage)})")
    
    traits_text = "\n".join(trait_analysis) if trait_analysis else "- No cognitive profile available (use baseline difficulty)"
    
    prompt = dedent(f"""
    You are an expert STEM educator creating personalized practice questions for adaptive learning.
    
    ## TOPIC INFORMATION
    **Topic**: {topic_title}
    **Description**: {topic_description}
    **Base Difficulty**: {difficulty}
    
    ## SOURCE MATERIAL (from uploaded PDF)
    {pdf_content[:3000]}  # Limit to avoid token overflow
    
    ## LEARNER'S COGNITIVE PROFILE
    {traits_text}
    
    ## 🎯 ADAPTIVE TARGETING STRATEGY (PHASE 2)
    {weakness_analysis.targeting_strategy}
    
    **IMPORTANT**: Follow this distribution carefully to address weaknesses while maintaining strengths.
    
    ## 🎚️ DIFFICULTY CALIBRATION (PHASE 3)
    **Calibrated Difficulty**: {calibrated_difficulty.overall_difficulty}
    {difficulty_guidance}
    
    **Rationale**: Questions are calibrated to learner's profile:
    - Weak traits ({', '.join(calibrated_difficulty.weak_traits) if calibrated_difficulty.weak_traits else 'none'}): Need foundational practice
    - Strong traits ({', '.join(calibrated_difficulty.strong_traits) if calibrated_difficulty.strong_traits else 'none'}): Ready for challenge
    
    ## KNOWN MISCONCEPTIONS TO ADDRESS (from database)
    {chr(10).join(f'- {m}' for m in misconception_texts) if misconception_texts else '- No specific misconceptions found in database - generate based on common patterns'}
    
    **IMPORTANT**: Use these misconceptions to craft realistic distractors that test for these specific errors.
    """)
    
    # PHASE 5: Add personal misconceptions if available
    if personal_misconceptions and len(personal_misconceptions) > 0:
        mc_list = []
        for mc in personal_misconceptions:
            mc_text = mc.get('misconception_text', '')
            severity = mc.get('severity', 'medium')
            frequency = mc.get('frequency', 1)
            mc_list.append(f"- {mc_text} (severity: {severity}, encountered {frequency}x)")
        
        personal_mc_section = f"""
    ## 🎯 STUDENT'S PERSONAL MISCONCEPTIONS (PRIORITY TARGETING - PHASE 5)
    This specific student has demonstrated these misconceptions in previous quizzes:
    {chr(10).join(mc_list)}
    
    **CRITICAL INSTRUCTION**: Generate questions that specifically test whether the student has overcome these personal misconceptions.
    Focus on creating scenarios where these misconceptions would lead to wrong answers if still present.
    This is REMEDIAL LEARNING - prioritize addressing these over general misconceptions.
    """
        prompt += personal_mc_section
        logger.info(f"🎯 [PHASE 5] Targeting {len(personal_misconceptions)} personal misconceptions")
    
    prompt += dedent("""
    
    ## YOUR TASK
    Generate ONE high-quality multiple-choice question that:
    
    1. **Tests Understanding**: Focus on conceptual understanding, not just memorization
    2. **Addresses Misconceptions**: Include distractors based on common student errors
    3. **Adapts to Profile (PHASE 2 ENHANCED)**: 
       - **PRIORITIZE weak traits** as specified in the adaptive strategy above
       - If analytical_depth is weak (<60%), use more scaffolding and clearer language
       - If precision is weak (<60%), focus on conceptual understanding rather than calculations
       - If curiosity is strong (>70%), include thought-provoking extensions
       - If metacognition is weak (<60%), focus on direct application rather than meta-analysis
    4. **Calibrated Difficulty (PHASE 3 ENHANCED)**:
       - Use the calibrated difficulty level ({calibrated_difficulty.overall_difficulty}) as your target
       - For weak traits: Provide more context, clearer wording, focus on core concepts
       - For strong traits: Include nuanced scenarios, multi-step reasoning, edge cases
    5. **Anchored to Content**: Base the question directly on the PDF material provided
    
    ## QUESTION STRUCTURE
    - **Stem**: Clear, focused question that tests a specific concept
    - **4 Options**: Exactly one correct answer + three carefully crafted distractors
      * Type "correct": The objectively correct answer
      * Type "misconception": Based on a common conceptual error
      * Type "partial": Shows partial understanding but incomplete
      * Type "procedural": Correct procedure but wrong application or conclusion
    
    ## OUTPUT FORMAT (JSON ONLY - NO MARKDOWN, NO EXPLANATIONS)
    {{
      "stem": "Your question stem here - be specific and clear",
      "options": [
        {{"text": "The correct answer with accurate reasoning", "type": "correct"}},
        {{"text": "Answer based on common misconception", "type": "misconception"}},
        {{"text": "Partially correct but missing key element", "type": "partial"}},
        {{"text": "Procedural error or misapplication", "type": "procedural"}}
      ],
      "explanation": "Brief explanation of why the correct answer is right and how each distractor represents a specific type of error",
      "difficulty": "{calibrated_difficulty.overall_difficulty}",
      "topic": "{topic_title}",
      "traits_targeted": ["precision", "analytical_depth"],
      "misconception_target": "Brief description of the main misconception this question addresses",
      "requires_calculation": true,
      "adaptive_reason": "Brief explanation of why this question was chosen for this learner (e.g., 'Targets weak precision trait (58%) with conceptual focus')"
    }}
    
    CRITICAL: 
    - Return ONLY the JSON object. No code fences, no commentary, no markdown.
    - Include ALL fields shown above, especially traits_targeted and adaptive_reason
    - Make sure "traits_targeted" lists the cognitive traits this question specifically tests
    - Make "adaptive_reason" explain why THIS question is personalized for THIS learner
    """)
    
    return prompt


def _interpret_trait(trait_name: str, percentage: int) -> str:
    """Provide human-readable interpretation of trait score."""
    if percentage >= 80:
        return "strong"
    elif percentage >= 60:
        return "developing"
    else:
        return "needs support"


def generate_questions_for_topics(
    topics: list[dict[str, Any]],
    pdf_content: str,
    cognitive_traits: dict[str, float],
    num_questions_per_topic: int = 2
) -> list[dict[str, Any]]:
    """
    Generate personalized questions for selected topics using GPT-4o.
    
    PHASE 3 ENHANCEMENT: Questions now include difficulty calibration metadata
    for research tracking of effectiveness.
    
    Args:
        topics: List of topic dicts with title, description, difficulty
        pdf_content: Extracted text from the PDF
        cognitive_traits: User's cognitive profile scores
        num_questions_per_topic: How many questions to generate per topic
    
    Returns:
        List of generated question objects with difficulty calibration metadata
    """
    client = _get_client()
    if not client:
        logger.error("OpenAI client not available - cannot generate questions")
        return []
    
    # PHASE 3: Get overall difficulty calibration once for efficiency
    from .difficulty_calibration import calibrate_difficulty_for_profile
    calibration = calibrate_difficulty_for_profile(cognitive_traits)
    
    all_questions = []
    
    for topic in topics:
        topic_title = topic.get("title", "Unknown Topic")
        topic_description = topic.get("description", "")
        difficulty = topic.get("difficulty", "intermediate").lower()
        
        logger.info(f"🎯 Generating {num_questions_per_topic} questions for topic: {topic_title}")
        
        # Extract subject_area from topic if available
        topic_subject_area = topic.get("subject_area") if isinstance(topic, dict) else None
        
        for i in range(num_questions_per_topic):
            try:
                prompt = build_question_generation_prompt(
                    topic_title=topic_title,
                    topic_description=topic_description,
                    pdf_content=pdf_content,
                    cognitive_traits=cognitive_traits,
                    difficulty=difficulty,
                    subject_area=topic_subject_area  # Pass subject area for domain filtering
                )
                
                response = client.chat.completions.create(
                    model=_settings.openai_model or "gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert STEM assessment designer. Return ONLY valid JSON with no markdown or explanations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.4,  # Balanced creativity and consistency
                    max_tokens=1000
                )
                
                content = response.choices[0].message.content
                if not content:
                    logger.warning(f"Empty response for topic {topic_title}")
                    continue
                
                # Strip markdown fences if present
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                # Parse JSON
                question_data = json.loads(content)
                
                # Validate structure
                required_fields = ["stem", "options", "explanation", "difficulty"]
                if not all(field in question_data for field in required_fields):
                    logger.warning(f"Missing required fields in question for {topic_title}")
                    continue
                
                if len(question_data.get("options", [])) != 4:
                    logger.warning(f"Question must have exactly 4 options for {topic_title}")
                    continue
                
                # Add metadata
                question_data["topic"] = topic_title
                question_data["question_number"] = len(all_questions) + 1
                
                # PHASE 3: Add difficulty calibration metadata for research tracking
                question_data["difficulty_calibration"] = {
                    "overall_recommendation": calibration.overall_difficulty,
                    "weak_traits_addressed": calibration.weak_traits,
                    "strong_traits_addressed": calibration.strong_traits,
                    "calibration_timestamp": None  # Will be set during quiz submission
                }
                
                all_questions.append(question_data)
                logger.info(f"✅ Generated question {i+1}/{num_questions_per_topic} for {topic_title} "
                           f"(difficulty: {calibration.overall_difficulty})")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON for {topic_title}: {e}")
                logger.error(f"Content was: {content[:200]}")
            except Exception as e:
                logger.error(f"Error generating question for {topic_title}: {e}", exc_info=True)
    
    logger.info(f"🎉 Total questions generated: {len(all_questions)} "
                f"(calibrated to {calibration.overall_difficulty} difficulty)")
    return all_questions


async def generate_questions_for_topics_with_semantic_context(
    topics: list[dict[str, Any]],
    pdf_content_by_topic: dict[str, str],
    cognitive_traits: dict[str, float],
    num_questions_per_topic: int = 2,
    extra_questions: int = 0,
    user_topic_traits: dict[str, dict] | None = None,
    user_id: str | None = None,  # PHASE 5: For personal misconception retrieval
    db=None  # PHASE 5: MongoDB database instance
) -> list[dict[str, Any]]:
    """
    Generate personalized questions using semantic search results.
    
    This function uses topic-specific content retrieved via semantic search,
    enabling true RAG (Retrieval-Augmented Generation).
    
    PHASE 3 ENHANCEMENT: Questions now include difficulty calibration metadata
    for research tracking of effectiveness.
    
    PHASE 4 ENHANCEMENT: Uses topic-specific traits when available for better personalization.
    
    PHASE 5 ENHANCEMENT: Retrieves and targets student's personal misconceptions
    for remedial learning.
    
    Args:
        topics: List of topic dicts with title, description, difficulty
        pdf_content_by_topic: Dict mapping topic title to relevant PDF content
        cognitive_traits: User's global cognitive profile scores (fallback)
        num_questions_per_topic: Base number of questions to generate per topic
        extra_questions: Additional questions to distribute across first topics
        user_topic_traits: Optional dict mapping topic names to topic-specific trait profiles
        user_id: User's ID for personal misconception retrieval (PHASE 5)
        db: MongoDB database instance for misconception queries (PHASE 5)
    
    Returns:
        List of generated question objects with difficulty calibration metadata
    """
    client = _get_client()
    if not client:
        logger.error("OpenAI client not available - cannot generate questions")
        return []
    
    # PHASE 3: Get overall difficulty calibration once for efficiency (using global traits)
    from .difficulty_calibration import calibrate_difficulty_for_profile
    calibration = calibrate_difficulty_for_profile(cognitive_traits)
    
    all_questions = []
    
    for topic_idx, topic in enumerate(topics):
        topic_title = topic.get("title", "Unknown Topic")
        topic_description = topic.get("description", "")
        difficulty = topic.get("difficulty", "intermediate").lower()
        
        # PHASE 4: Use topic-specific traits if available, otherwise use global
        traits_for_this_topic = cognitive_traits
        if user_topic_traits and topic_title in user_topic_traits:
            topic_profile = user_topic_traits[topic_title]
            if isinstance(topic_profile, dict) and 'traits' in topic_profile:
                # Extract traits from TopicTraitProfile
                topic_specific = topic_profile['traits']
                if isinstance(topic_specific, dict):
                    traits_for_this_topic = topic_specific
                    logger.info(f"✅ Using topic-specific traits for '{topic_title}': {traits_for_this_topic}")
                elif hasattr(topic_specific, 'model_dump'):
                    traits_for_this_topic = topic_specific.model_dump()
                    logger.info(f"✅ Using topic-specific traits for '{topic_title}' (from model)")
        
        # Calculate questions for this topic (distribute extra questions to first topics)
        questions_for_this_topic = num_questions_per_topic
        if extra_questions > 0 and topic_idx < extra_questions:
            questions_for_this_topic += 1
        
        # Get semantically retrieved content for this specific topic
        topic_content = pdf_content_by_topic.get(topic_title, "")
        
        if not topic_content:
            logger.warning(f"⚠️ No semantic content found for topic: {topic_title}, skipping...")
            continue
        
        logger.info(f"🎯 Generating {questions_for_this_topic} questions for topic: {topic_title}")
        logger.info(f"📄 Using {len(topic_content)} chars of semantically retrieved content")
        
        # PHASE 5: Retrieve personal misconceptions for this topic
        personal_misconceptions = []
        if user_id is not None and db is not None:  # Fixed: MongoDB objects can't use boolean context
            try:
                personal_mcs = await get_user_personal_misconceptions(
                    db=db,
                    user_id=user_id,
                    topic=topic_title,
                    only_unresolved=True
                )
                if personal_mcs:
                    # Convert to dict format for prompt
                    personal_misconceptions = [
                        {
                            "misconception_text": mc.misconception_text,
                            "severity": mc.severity,
                            "frequency": mc.frequency
                        }
                        for mc in personal_mcs
                    ]
                    logger.info(f"🎯 [PHASE 5] Found {len(personal_misconceptions)} unresolved misconceptions for '{topic_title}'")
            except Exception as mc_error:
                logger.warning(f"Could not retrieve personal misconceptions: {mc_error}")
        
        # Track questions for this topic to avoid duplicates
        topic_questions = []
        
        # Extract subject_area from topic if available
        topic_subject_area = topic.get("subject_area") if isinstance(topic, dict) else None
        
        for i in range(questions_for_this_topic):
            try:
                # Build prompt with context of previous questions to avoid duplicates
                previous_questions_context = ""
                if topic_questions:
                    previous_questions_context = "\n\n## IMPORTANT: AVOID DUPLICATES\nYou have already generated these questions for this topic:\n"
                    for idx, prev_q in enumerate(topic_questions, 1):
                        previous_questions_context += f"{idx}. {prev_q.get('stem', '')}\n"
                    previous_questions_context += "\n**Generate a DIFFERENT question that tests a DIFFERENT aspect or sub-concept of this topic.**\n"
                
                prompt = build_question_generation_prompt(
                    topic_title=topic_title,
                    topic_description=topic_description,
                    pdf_content=topic_content,  # ← Semantically retrieved content!
                    cognitive_traits=traits_for_this_topic,  # ← Use topic-specific or global
                    difficulty=difficulty,
                    personal_misconceptions=personal_misconceptions,  # PHASE 5: Target personal misconceptions
                    subject_area=topic_subject_area  # Pass subject area for domain filtering
                )
                
                # Append duplicate prevention context
                prompt += previous_questions_context
                
                response = client.chat.completions.create(
                    model=_settings.openai_model or "gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert STEM assessment designer. Return ONLY valid JSON with no markdown or explanations. Generate diverse questions that test different aspects of the topic."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,  # Higher temperature for more diversity
                    max_tokens=1000
                )
                
                content = response.choices[0].message.content
                if not content:
                    logger.warning(f"Empty response for topic {topic_title}")
                    continue
                
                # Strip markdown fences if present
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                # Parse JSON
                question_data = json.loads(content)
                
                # Validate structure
                required_fields = ["stem", "options", "explanation", "difficulty"]
                if not all(field in question_data for field in required_fields):
                    logger.warning(f"Missing required fields in question for {topic_title}")
                    continue
                
                if len(question_data.get("options", [])) != 4:
                    logger.warning(f"Question must have exactly 4 options for {topic_title}")
                    continue
                
                # Add metadata
                question_data["topic"] = topic_title
                question_data["question_number"] = len(all_questions) + 1
                
                # PHASE 3: Add difficulty calibration metadata for research tracking
                question_data["difficulty_calibration"] = {
                    "overall_recommendation": calibration.overall_difficulty,
                    "weak_traits_addressed": calibration.weak_traits,
                    "strong_traits_addressed": calibration.strong_traits,
                    "calibration_timestamp": None  # Will be set during quiz submission
                }
                
                topic_questions.append(question_data)
                all_questions.append(question_data)
                logger.info(f"✅ Generated question {i+1}/{questions_for_this_topic} for {topic_title} "
                           f"(difficulty: {calibration.overall_difficulty})")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON for {topic_title}: {e}")
                if 'content' in locals():
                    logger.error(f"Content was: {content[:200]}")
            except Exception as e:
                logger.error(f"Error generating question for {topic_title}: {e}", exc_info=True)
    
    logger.info(f"🎉 Total questions generated: {len(all_questions)} across {len(topics)} topics "
                f"(calibrated to {calibration.overall_difficulty} difficulty)")
    return all_questions

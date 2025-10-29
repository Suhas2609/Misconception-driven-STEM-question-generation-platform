"""
Service for generating questions from selected topics using GPT-4o.
This is the CORE PROMPT ENGINEERING for personalized question generation.
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


def build_question_generation_prompt(
    topic_title: str,
    topic_description: str,
    pdf_content: str,
    cognitive_traits: dict[str, float],
    difficulty: str = "intermediate"
) -> str:
    """
    Build the GPT-4o prompt for generating personalized STEM questions.
    
    This is the MAIN PROMPT ENGINEERING task - it combines:
    - Topic from PDF extraction
    - User's cognitive profile
    - PDF content (RAG)
    - Common misconceptions
    """
    
    # Format cognitive traits for the prompt
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
    **Target Difficulty**: {difficulty}
    
    ## SOURCE MATERIAL (from uploaded PDF)
    {pdf_content[:3000]}  # Limit to avoid token overflow
    
    ## LEARNER'S COGNITIVE PROFILE
    {traits_text}
    
    ## COMMON MISCONCEPTIONS TO ADDRESS
    Based on the topic "{topic_title}", students often struggle with:
    - Confusing similar concepts or terminology
    - Applying procedures without understanding underlying principles
    - Making incorrect assumptions about cause-and-effect relationships
    - Overgeneralizing from specific examples
    
    ## YOUR TASK
    Generate ONE high-quality multiple-choice question that:
    
    1. **Tests Understanding**: Focus on conceptual understanding, not just memorization
    2. **Addresses Misconceptions**: Include distractors based on common student errors
    3. **Adapts to Profile**: 
       - If analytical_reasoning is low (<60%), use more scaffolding and clearer language
       - If pattern_recognition is high (>70%), include subtle patterns or relationships
       - If metacognitive_awareness is low (<60%), focus on direct application rather than meta-analysis
       - If fermi_estimation is high (>70%), you can include quantitative reasoning
    4. **Anchored to Content**: Base the question directly on the PDF material provided
    5. **Appropriate Difficulty**: Match the specified difficulty level
    
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
      "difficulty": "{difficulty}",
      "topic": "{topic_title}"
    }}
    
    CRITICAL: Return ONLY the JSON object. No code fences, no commentary, no markdown.
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
    
    Args:
        topics: List of topic dicts with title, description, difficulty
        pdf_content: Extracted text from the PDF
        cognitive_traits: User's cognitive profile scores
        num_questions_per_topic: How many questions to generate per topic
    
    Returns:
        List of generated question objects
    """
    client = _get_client()
    if not client:
        logger.error("OpenAI client not available - cannot generate questions")
        return []
    
    all_questions = []
    
    for topic in topics:
        topic_title = topic.get("title", "Unknown Topic")
        topic_description = topic.get("description", "")
        difficulty = topic.get("difficulty", "intermediate").lower()
        
        logger.info(f"🎯 Generating {num_questions_per_topic} questions for topic: {topic_title}")
        
        for i in range(num_questions_per_topic):
            try:
                prompt = build_question_generation_prompt(
                    topic_title=topic_title,
                    topic_description=topic_description,
                    pdf_content=pdf_content,
                    cognitive_traits=cognitive_traits,
                    difficulty=difficulty
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
                
                all_questions.append(question_data)
                logger.info(f"✅ Generated question {i+1}/{num_questions_per_topic} for {topic_title}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON for {topic_title}: {e}")
                logger.error(f"Content was: {content[:200]}")
            except Exception as e:
                logger.error(f"Error generating question for {topic_title}: {e}", exc_info=True)
    
    logger.info(f"🎉 Total questions generated: {len(all_questions)}")
    return all_questions


def generate_questions_for_topics_with_semantic_context(
    topics: list[dict[str, Any]],
    pdf_content_by_topic: dict[str, str],
    cognitive_traits: dict[str, float],
    num_questions_per_topic: int = 2,
    extra_questions: int = 0
) -> list[dict[str, Any]]:
    """
    Generate personalized questions using semantic search results.
    
    This function uses topic-specific content retrieved via semantic search,
    enabling true RAG (Retrieval-Augmented Generation).
    
    Args:
        topics: List of topic dicts with title, description, difficulty
        pdf_content_by_topic: Dict mapping topic title to relevant PDF content
        cognitive_traits: User's cognitive profile scores
        num_questions_per_topic: Base number of questions to generate per topic
        extra_questions: Additional questions to distribute across first topics
    
    Returns:
        List of generated question objects
    """
    client = _get_client()
    if not client:
        logger.error("OpenAI client not available - cannot generate questions")
        return []
    
    all_questions = []
    
    for topic_idx, topic in enumerate(topics):
        topic_title = topic.get("title", "Unknown Topic")
        topic_description = topic.get("description", "")
        difficulty = topic.get("difficulty", "intermediate").lower()
        
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
        
        # Track questions for this topic to avoid duplicates
        topic_questions = []
        
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
                    cognitive_traits=cognitive_traits,
                    difficulty=difficulty
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
                
                # Add to global list
                all_questions.append(question_data)
                
                # Add to topic tracking list to prevent duplicates in next iteration
                topic_questions.append(question_data)
                
                logger.info(f"✅ Generated question {i+1}/{questions_for_this_topic} for {topic_title} using RAG")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON for {topic_title}: {e}")
                logger.error(f"Content was: {content[:200] if 'content' in locals() else 'N/A'}")
            except Exception as e:
                logger.error(f"Error generating question for {topic_title}: {e}", exc_info=True)
    
    logger.info(f"🎉 Total questions generated with semantic RAG: {len(all_questions)}")
    return all_questions

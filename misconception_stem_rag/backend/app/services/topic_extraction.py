"""Topic extraction service using GPT-4o to identify STEM concepts from PDF content."""

from __future__ import annotations

import json
import logging
from textwrap import dedent
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from ..config import get_settings

logger = logging.getLogger(__name__)


class ExtractedTopic(BaseModel):
    """A single STEM topic/concept extracted from the document."""

    title: str = Field(description="Concise topic name (2-5 words)")
    description: str = Field(description="Brief explanation of the concept")
    difficulty: str = Field(description="estimated | easy | medium | hard | advanced")
    keywords: list[str] = Field(default_factory=list, description="Related keywords/terms")
    prerequisites: list[str] = Field(default_factory=list, description="Required prior knowledge")
    subject_area: str = Field(description="physics | chemistry | biology | mathematics | engineering | computer_science")


class TopicExtractionResult(BaseModel):
    """Complete result of topic extraction from a document."""

    topics: list[ExtractedTopic]
    document_summary: str = Field(description="One-paragraph summary of the document's scope")
    recommended_order: list[str] = Field(
        default_factory=list,
        description="Suggested learning order (topic titles)"
    )


def extract_topics_from_text(text: str, filename: str = "document") -> TopicExtractionResult:
    """
    Use GPT-4o to extract structured STEM topics from PDF text content.
    
    This is the CORE prompt for topic extraction - uses chain-of-thought reasoning
    to identify concepts, assess difficulty, and suggest learning paths.
    
    Args:
        text: Full or chunked text from the PDF
        filename: Original filename for context
        
    Returns:
        TopicExtractionResult with extracted topics and metadata
    """
    logger.info(f"🔍 Extracting topics from {filename} ({len(text)} chars)")
    
    settings = get_settings()
    if not settings.openai_api_key or "REDACTED" in settings.openai_api_key:
        logger.warning("⚠️ No OpenAI API key - returning empty topic list")
        return TopicExtractionResult(
            topics=[],
            document_summary="API key not configured",
            recommended_order=[]
        )
    
    # Truncate text if too long (GPT-4o context window is 128k, but we'll be conservative)
    max_chars = 50000  # ~12k tokens
    if len(text) > max_chars:
        logger.info(f"📄 Truncating text from {len(text)} to {max_chars} chars")
        text = text[:max_chars] + "\n\n[... document continues ...]"
    
    prompt = dedent(
        f"""
        You are an expert STEM educator analyzing educational content to extract key learning topics.
        
        **Your Task:**
        Analyze the following document and identify the main STEM concepts, theories, or skills that a student should learn.
        For each topic, assess its difficulty, identify prerequisites, and note related keywords.
        
        **Document:** {filename}
        **Content:**
        {text}
        
        **Instructions:**
        1. **Identify 5-15 distinct topics** (not too granular, not too broad)
           - Focus on core concepts, not every minor detail
           - Each topic should be quiz-worthy (can generate 3+ questions)
        
        2. **For each topic, provide:**
           - **title**: Clear, concise name (e.g., "Newton's Second Law", "Mitochondrial Respiration")
           - **description**: 1-2 sentence explanation of what this concept covers
           - **difficulty**: One of [easy, medium, hard, advanced] based on typical student level
           - **keywords**: 3-5 related terms/synonyms students should know
           - **prerequisites**: What should students understand BEFORE learning this topic?
           - **subject_area**: Primary STEM domain (physics, chemistry, biology, mathematics, engineering, computer_science)
        
        3. **Provide a document summary** (1 paragraph) describing the overall scope and purpose
        
        4. **Suggest a learning order** (list of topic titles in recommended sequence)
           - Consider: prerequisites → foundational → advanced
           - Build complexity gradually
        
        **Quality Guidelines:**
        - Avoid redundancy: merge similar concepts into one topic
        - Be specific: "Kinematics in 1D" > "Motion"
        - Think pedagogically: what would make a good quiz section?
        - Respect cognitive load: don't overwhelm with 30 micro-topics
        
        Return **only** valid JSON matching this schema:
        {{
          "topics": [
            {{
              "title": "Topic Name",
              "description": "What this covers...",
              "difficulty": "medium",
              "keywords": ["term1", "term2"],
              "prerequisites": ["prior concept"],
              "subject_area": "physics"
            }}
          ],
          "document_summary": "This document covers...",
          "recommended_order": ["Topic 1", "Topic 2", ...]
        }}
        """
    ).strip()
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    try:
        logger.info(f"🤖 Calling GPT-4o for topic extraction (model: {settings.openai_model or 'gpt-4o'})")
        
        response = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert STEM curriculum analyst. Return only valid JSON, no markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temp for consistent extraction
            max_tokens=3000,  # Allow detailed responses
        )
        
        content = response.choices[0].message.content
        if not content:
            logger.error("❌ GPT returned empty response")
            return _fallback_extraction(text, filename)
        
        logger.info(f"✅ Received response from GPT ({len(content)} chars)")
        
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON
        parsed = json.loads(content)
        logger.info("✅ Successfully parsed JSON from GPT response")
        
        # Validate and construct result
        result = TopicExtractionResult(
            topics=[ExtractedTopic(**t) for t in parsed.get("topics", [])],
            document_summary=parsed.get("document_summary", "No summary provided"),
            recommended_order=parsed.get("recommended_order", [])
        )
        
        logger.info(f"🎯 Extracted {len(result.topics)} topics from {filename}")
        for topic in result.topics:
            logger.info(f"  • {topic.title} ({topic.difficulty}) - {topic.subject_area}")
        
        return result
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing failed: {e}")
        logger.error(f"Raw GPT response: {content[:500]}...")
        return _fallback_extraction(text, filename)
    
    except Exception as e:
        logger.error(f"❌ Topic extraction failed: {type(e).__name__}: {e}")
        return _fallback_extraction(text, filename)


def _fallback_extraction(text: str, filename: str) -> TopicExtractionResult:
    """
    Fallback heuristic topic extraction when GPT fails.
    Uses simple keyword matching and text structure.
    """
    logger.warning("⚠️ Using fallback topic extraction")
    
    # Simple heuristic: look for chapter/section headers
    lines = text.split("\n")
    topics = []
    
    for line in lines[:100]:  # Only check first 100 lines
        line = line.strip()
        # Look for patterns like "Chapter 3:", "3.1 Topic Name", etc.
        if any(keyword in line.lower() for keyword in ["chapter", "section", "lesson", "topic"]):
            if 10 < len(line) < 100:  # Reasonable title length
                topics.append(
                    ExtractedTopic(
                        title=line[:50],  # Truncate long titles
                        description="Auto-detected from document structure",
                        difficulty="medium",
                        keywords=[],
                        prerequisites=[],
                        subject_area="physics"  # Default guess
                    )
                )
    
    if not topics:
        # Ultimate fallback: create generic topic from filename
        topics.append(
            ExtractedTopic(
                title=filename.replace(".pdf", "").replace("_", " "),
                description="General content from uploaded document",
                difficulty="medium",
                keywords=[],
                prerequisites=[],
                subject_area="physics"
            )
        )
    
    return TopicExtractionResult(
        topics=topics[:10],  # Limit to 10
        document_summary=f"Content extracted from {filename}",
        recommended_order=[t.title for t in topics[:10]]
    )

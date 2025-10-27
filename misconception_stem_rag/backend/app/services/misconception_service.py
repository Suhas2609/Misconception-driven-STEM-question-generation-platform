"""Misconception management service - CORE research contribution.

This module handles:
1. Loading misconceptions from CSV files (domain expert knowledge)
2. GPT-4o synthesis of new misconceptions for sparse topics
3. Mining misconceptions from user quiz feedback
4. Semantic retrieval of relevant misconceptions for question generation
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from ..config import settings
from ..db.mongo import get_collection
from ..services.semantic_search import get_semantic_search_service

logger = logging.getLogger(__name__)


class MisconceptionService:
    """Service for managing and retrieving misconceptions."""
    
    def __init__(self):
        """Initialize misconception service with OpenAI and semantic search."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.semantic_service = get_semantic_search_service()
        self.misconceptions_collection = get_collection("misconceptions")
        self.ai_misconceptions_collection = get_collection("ai_generated_misconceptions")
        logger.info("✅ Misconception service initialized")
    
    async def seed_from_csv(self, csv_path: str | Path) -> int:
        """
        Load misconceptions from CSV file and store in MongoDB + ChromaDB.
        
        CSV Format (flexible - supports multiple formats):
        Format 1: pattern,correct_concept,subject_area,topic,difficulty,source
        Format 2: subject,concept,misconception_text,correction
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Number of misconceptions loaded
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            logger.error(f"❌ CSV file not found: {csv_path}")
            return 0
        
        try:
            misconceptions = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                logger.info(f"📄 CSV headers: {headers}")
                
                for row in reader:
                    # Support Format 1: pattern,correct_concept,subject_area,topic,difficulty
                    if "pattern" in headers and "correct_concept" in headers:
                        misconception = {
                            "pattern": row.get("pattern", "").strip(),
                            "correct_concept": row.get("correct_concept", "").strip(),
                            "subject_area": row.get("subject_area", "").strip().lower(),
                            "topic": row.get("topic", "").strip(),
                            "difficulty": row.get("difficulty", "medium").strip().lower(),
                            "source": "csv_seed",
                            "validated": True,
                            "confidence": 1.0,
                            "created_at": datetime.utcnow()
                        }
                    
                    # Support Format 2: subject,concept,misconception_text,correction
                    elif "misconception_text" in headers and "correction" in headers:
                        misconception = {
                            "pattern": row.get("misconception_text", "").strip(),
                            "correct_concept": row.get("correction", "").strip(),
                            "subject_area": row.get("subject", "").strip().lower(),
                            "topic": row.get("concept", "").strip(),
                            "difficulty": "medium",  # Default difficulty
                            "source": "csv_seed",
                            "validated": True,
                            "confidence": 1.0,
                            "created_at": datetime.utcnow()
                        }
                    
                    else:
                        logger.warning(f"⚠️ Unsupported CSV format. Headers: {headers}")
                        continue
                    
                    if misconception["pattern"] and misconception["correct_concept"]:
                        misconceptions.append(misconception)
            
            if misconceptions:
                # Store in MongoDB
                result = await self.misconceptions_collection.insert_many(misconceptions)
                logger.info(f"📚 Inserted {len(result.inserted_ids)} misconceptions into MongoDB")
                
                # Embed in ChromaDB for semantic search
                documents = [m["pattern"] for m in misconceptions]
                metadatas = [
                    {
                        "subject": m["subject_area"],
                        "topic": m["topic"],
                        "difficulty": m["difficulty"],
                        "source": "csv_seed"
                    }
                    for m in misconceptions
                ]
                ids = [str(m_id) for m_id in result.inserted_ids]
                
                self.semantic_service.add_documents(
                    collection_name="misconceptions",
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"✅ Seeded {len(misconceptions)} misconceptions from {csv_path.name}")
                return len(misconceptions)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error seeding misconceptions from CSV: {e}")
            raise
    
    def synthesize_misconceptions_for_topic(
        self,
        topic: str,
        subject_area: str,
        num_misconceptions: int = 5
    ) -> list[dict[str, Any]]:
        """
        Use GPT-4o to generate realistic misconceptions for a topic.
        
        This is GPT-4o Prompt #6: Misconception Synthesis
        
        Args:
            topic: Topic name (e.g., "SN1 vs SN2 Reactions")
            subject_area: Subject (e.g., "organic_chemistry")
            num_misconceptions: How many to generate
            
        Returns:
            List of synthesized misconception dicts
        """
        try:
            prompt = f"""You are an expert STEM educator with deep knowledge of common student misconceptions.

Generate {num_misconceptions} realistic misconceptions for this topic:
**Topic**: {topic}
**Subject**: {subject_area}

Each misconception should:
1. Reflect actual cognitive errors students make
2. Be specific and grounded in the topic
3. Include the correct concept for comparison

Return ONLY valid JSON (no markdown):
[
  {{
    "pattern": "Students think SN1 reactions require strong nucleophiles",
    "correct_concept": "SN1 depends on carbocation stability, not nucleophile strength",
    "difficulty": "medium",
    "reasoning": "Students confuse SN1 and SN2 mechanisms"
  }}
]

Focus on conceptual misunderstandings, not simple factual errors."""

            response = self.client.chat.completions.create(
                model=settings.openai_model or "gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in student learning and common misconceptions. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty response from GPT-4o for misconception synthesis")
                return []
            
            # Strip markdown fences
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            misconceptions_data = json.loads(content)
            
            # Add metadata
            for m in misconceptions_data:
                m["subject_area"] = subject_area
                m["topic"] = topic
                m["source"] = "gpt4o_synthesis"
                m["validated"] = False  # Requires validation
                m["confidence"] = 0.7   # Medium confidence for AI-generated
                m["created_at"] = datetime.utcnow()
            
            logger.info(f"✅ Synthesized {len(misconceptions_data)} misconceptions for '{topic}'")
            return misconceptions_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4o misconception JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error synthesizing misconceptions: {e}")
            return []
    
    async def mine_misconception_from_feedback(
        self,
        question_text: str,
        user_answer: str,
        correct_answer: str,
        user_reasoning: str,
        topic: str,
        subject_area: str
    ) -> dict[str, Any] | None:
        """
        Extract misconception pattern from user's incorrect response.
        
        This is GPT-4o Prompt #7: Misconception Mining
        
        Args:
            question_text: The question asked
            user_answer: User's selected answer (wrong)
            correct_answer: The correct answer
            user_reasoning: User's explanation (if provided)
            topic: Topic of the question
            subject_area: Subject area
            
        Returns:
            Extracted misconception dict or None
        """
        try:
            prompt = f"""Analyze this student's incorrect response to identify the underlying misconception.

**Question**: {question_text}

**Student's Answer**: {user_answer}
**Correct Answer**: {correct_answer}
**Student's Reasoning**: {user_reasoning or "Not provided"}

Extract the misconception pattern as a general statement that could apply to other students.

Return ONLY valid JSON:
{{
  "pattern": "A concise statement of the misconception (e.g., 'Students think X causes Y')",
  "correct_concept": "The correct understanding",
  "confidence": 0.8,
  "reasoning": "Why this represents a misconception vs simple error"
}}

If this is just a random guess (not a conceptual error), return {{"pattern": null}}"""

            response = self.client.chat.completions.create(
                model=settings.openai_model or "gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at diagnosing student learning gaps. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Very low temperature for analysis
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
            
            # Strip markdown
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            result = json.loads(content)
            
            if not result.get("pattern"):
                logger.info("⚠️ No misconception pattern identified (likely random guess)")
                return None
            
            # Add metadata
            misconception = {
                "pattern": result["pattern"],
                "correct_concept": result.get("correct_concept", ""),
                "subject_area": subject_area,
                "topic": topic,
                "source": "user_feedback",
                "validated": False,  # Needs review
                "confidence": result.get("confidence", 0.5),
                "created_at": datetime.utcnow(),
                "sample_question": question_text,
                "sample_user_answer": user_answer
            }
            
            # Store in AI-generated misconceptions collection
            await self.ai_misconceptions_collection.insert_one(misconception)
            logger.info(f"💡 Mined new misconception from user feedback: '{result['pattern']}'")
            
            return misconception
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse misconception mining JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error mining misconception: {e}")
            return None
    
    def retrieve_misconceptions_for_topic(
        self,
        topic: str,
        subject_area: str | None = None,
        n_results: int = 3
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant misconceptions for a topic using semantic search.
        
        Args:
            topic: Topic name or description
            subject_area: Optional subject filter
            n_results: Number of misconceptions to retrieve
            
        Returns:
            List of misconception dicts with pattern and correct_concept
        """
        try:
            # Build metadata filter
            where_filter = {}
            if subject_area:
                where_filter["subject"] = subject_area
            
            # Semantic search in misconceptions collection
            results = self.semantic_service.semantic_search(
                collection_name="misconceptions",
                query=topic,
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            if results["documents"]:
                misconceptions = [
                    {
                        "pattern": doc,
                        "metadata": meta,
                        "relevance_score": 1 - dist  # Convert distance to similarity
                    }
                    for doc, meta, dist in zip(
                        results["documents"],
                        results["metadatas"],
                        results["distances"]
                    )
                ]
                logger.info(f"🔍 Retrieved {len(misconceptions)} misconceptions for '{topic}'")
                return misconceptions
            
            logger.warning(f"⚠️ No misconceptions found for topic '{topic}'")
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving misconceptions: {e}")
            return []


# Singleton instance
_misconception_service = None


def get_misconception_service() -> MisconceptionService:
    """Get or create the singleton MisconceptionService instance."""
    global _misconception_service
    if _misconception_service is None:
        _misconception_service = MisconceptionService()
    return _misconception_service

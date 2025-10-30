"""
AI-Powered Misconception Extraction Service

Extracts misconceptions from student quiz responses using GPT-4o.
Stores discovered misconceptions in both MongoDB (personal tracking) and ChromaDB (global knowledge base).
"""
import logging
from typing import Optional, List, Any
from datetime import datetime
import json
import uuid

from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from ..models.misconception import (
    DiscoveredMisconception,
    PersonalMisconception,
    MisconceptionResolutionEvent
)
from ..db.chroma import get_client as get_chroma_client

logger = logging.getLogger(__name__)

# Initialize OpenAI
openai_client = AsyncOpenAI()

# Sentence transformer for embeddings
_embedder: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    """Lazy load sentence transformer."""
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedder


async def extract_misconception_from_response(
    question_text: str,
    correct_option: str,
    selected_option: str,
    reasoning: str,
    topic: str,
    all_options: Optional[List[str]] = None
) -> Optional[DiscoveredMisconception]:
    """
    Use GPT-4o to identify the underlying misconception from a wrong answer.
    
    Args:
        question_text: The question that was asked
        correct_option: The correct answer
        selected_option: What the student selected (wrong)
        reasoning: Student's reasoning/explanation
        topic: Topic/domain of the question
        all_options: All available options (for context)
        
    Returns:
        DiscoveredMisconception if a clear misconception is identified, None otherwise
    """
    try:
        prompt = f"""You are an expert educational psychologist specializing in misconception analysis.

Analyze this student's incorrect response and identify the underlying misconception.

**QUESTION:** {question_text}

**CORRECT ANSWER:** {correct_option}

**STUDENT'S ANSWER:** {selected_option}

**STUDENT'S REASONING:** {reasoning}

**TOPIC:** {topic}

{"**ALL OPTIONS:** " + str(all_options) if all_options else ""}

**TASK:**
Identify the core misconception that led the student to choose the wrong answer.

Return a JSON object with:
{{
    "misconception_text": "Clear, concise description of the misconception (e.g., 'Confuses checked vs unchecked exceptions')",
    "confidence": 0.0-1.0 (how confident you are this is the misconception),
    "evidence": "Specific evidence from the reasoning that reveals this misconception",
    "severity": "low" | "medium" | "high" | "critical",
    "related_trait": "Which cognitive trait this affects most (precision, analytical_depth, etc.)",
    "suggested_remediation": "Brief suggestion for addressing this misconception"
}}

If the student just guessed or no clear misconception is evident, return {{"misconception_text": null}}
"""

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at identifying student misconceptions from their responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for consistent analysis
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Check if misconception was identified
        if not result.get("misconception_text"):
            logger.info(f"No clear misconception identified for topic '{topic}'")
            return None
            
        misconception = DiscoveredMisconception(
            misconception_text=result["misconception_text"],
            topic=topic,
            confidence=result.get("confidence", 0.8),
            evidence=result.get("evidence", reasoning),
            severity=result.get("severity", "medium"),
            related_trait=result.get("related_trait"),
            suggested_remediation=result.get("suggested_remediation")
        )
        
        logger.info(f"✅ Extracted misconception: '{misconception.misconception_text}' (confidence: {misconception.confidence})")
        return misconception
        
    except Exception as e:
        logger.error(f"Error extracting misconception: {e}", exc_info=True)
        return None


async def store_personal_misconception(
    db: Any,  # MongoDB database instance
    user_id: str,
    discovered: DiscoveredMisconception,
    question_context: str,
    student_reasoning: str
) -> PersonalMisconception:
    """
    Store a discovered misconception in the user's personal misconception history.
    
    If the same misconception already exists, increments frequency instead of creating duplicate.
    
    Args:
        db: MongoDB database instance
        user_id: User's ID
        discovered: The discovered misconception
        question_context: Original question text
        student_reasoning: Student's reasoning
        
    Returns:
        PersonalMisconception object (new or updated)
    """
    try:
        users_collection = db.get_collection("users")
        user = await users_collection.find_one({"_id": user_id})
        
        if not user:
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User {user_id} not found")
        
        # Get existing misconceptions for this topic
        personal_misconceptions = user.get("personal_misconceptions", {})
        topic_misconceptions = personal_misconceptions.get(discovered.topic, [])
        
        # Check if similar misconception already exists
        existing = None
        for mc in topic_misconceptions:
            # Simple similarity check (can be improved with semantic similarity)
            if mc.get("misconception_text", "").lower() == discovered.misconception_text.lower():
                existing = mc
                break
        
        if existing:
            # Update existing misconception
            logger.info(f"📊 Updating existing misconception frequency: '{discovered.misconception_text}'")
            
            await users_collection.update_one(
                {
                    "_id": user_id,
                    f"personal_misconceptions.{discovered.topic}.misconception_id": existing["misconception_id"]
                },
                {
                    "$inc": {f"personal_misconceptions.{discovered.topic}.$.frequency": 1},
                    "$set": {
                        f"personal_misconceptions.{discovered.topic}.$.last_occurrence": datetime.utcnow().isoformat(),
                        f"personal_misconceptions.{discovered.topic}.$.resolved": False,  # Reset if they got it wrong again
                        f"personal_misconceptions.{discovered.topic}.$.correct_streak": 0
                    }
                }
            )
            
            existing["frequency"] += 1
            existing["last_occurrence"] = datetime.utcnow().isoformat()
            return PersonalMisconception(**existing)
        else:
            # Create new misconception
            logger.info(f"🆕 Storing new personal misconception: '{discovered.misconception_text}'")
            
            new_misconception = PersonalMisconception(
                misconception_id=str(uuid.uuid4()),
                misconception_text=discovered.misconception_text,
                topic=discovered.topic,
                question_context=question_context,
                student_reasoning=student_reasoning,
                first_encountered=datetime.utcnow(),
                frequency=1,
                last_occurrence=datetime.utcnow(),
                resolved=False,
                correct_streak=0,
                targeted_question_count=0,
                severity=discovered.severity,
                related_trait=discovered.related_trait
            )
            
            # Add to user's misconceptions
            await users_collection.update_one(
                {"_id": user_id},
                {
                    "$push": {
                        f"personal_misconceptions.{discovered.topic}": new_misconception.model_dump()
                    }
                }
            )
            
            return new_misconception
            
    except Exception as e:
        logger.error(f"Error storing personal misconception: {e}", exc_info=True)
        raise


async def check_and_promote_misconception_to_global(
    db: Any,  # MongoDB database for frequency checking
    misconception_text: str,
    topic: str,
    domain: str,
    frequency_threshold: int = 3,
    similarity_threshold: float = 0.85
) -> dict:
    """
    Check if misconception should be promoted to global KB with novelty detection.
    
    Promotion Logic:
    1. Check novelty: similarity to existing global misconceptions < similarity_threshold
    2. Check frequency: appears in >= frequency_threshold different students
    3. If both pass, add to ChromaDB global database
    
    Args:
        db: MongoDB database instance
        misconception_text: The misconception to potentially promote
        topic: Topic name
        domain: Subject area (Physics, Chemistry, etc.)
        frequency_threshold: Minimum number of students who must have this misconception
        similarity_threshold: Maximum similarity to existing (0-1, higher = stricter novelty)
        
    Returns:
        dict with promotion status and details
    """
    try:
        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection(name="misconceptions")
        
        # Step 1: Novelty Detection using semantic similarity
        embedder = get_embedder()
        embedding = embedder.encode(misconception_text).tolist()
        
        # Query for similar misconceptions in same domain
        similar_results = collection.query(
            query_embeddings=[embedding],
            n_results=3,
            where={"subject": domain} if domain else None
        )
        
        # Calculate max similarity (ChromaDB returns L2 distances, convert to cosine similarity)
        max_similarity = 0.0
        most_similar_text = None
        
        if similar_results and similar_results['distances'] and len(similar_results['distances'][0]) > 0:
            # Convert L2 distance to similarity (approximate)
            min_distance = similar_results['distances'][0][0]
            max_similarity = 1.0 - (min_distance / 2.0)  # Rough conversion
            most_similar_text = similar_results['documents'][0][0] if similar_results['documents'] else None
        
        # Check novelty threshold
        if max_similarity >= similarity_threshold:
            logger.info(
                f"⚠️ Misconception too similar to existing (sim={max_similarity:.2f}): "
                f"'{misconception_text[:50]}...' ≈ '{most_similar_text[:50] if most_similar_text else 'N/A'}...'"
            )
            return {
                "promoted": False,
                "reason": "duplicate",
                "similarity": max_similarity,
                "similar_to": most_similar_text
            }
        
        # Step 2: Frequency Check across all users
        users_collection = db.get_collection("users")
        
        # Count unique students who have this misconception
        # Search across all topics in personal_misconceptions
        pipeline = [
            {"$match": {"personal_misconceptions": {"$exists": True}}},
            {"$project": {
                "has_misconception": {
                    "$anyElementTrue": {
                        "$map": {
                            "input": {"$objectToArray": "$personal_misconceptions"},
                            "as": "topic_entry",
                            "in": {
                                "$anyElementTrue": {
                                    "$map": {
                                        "input": "$$topic_entry.v",
                                        "as": "mc",
                                        "in": {
                                            "$regexMatch": {
                                                "input": {"$ifNull": ["$$mc.misconception_text", ""]},
                                                "regex": misconception_text,
                                                "options": "i"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }},
            {"$match": {"has_misconception": True}},
            {"$count": "student_count"}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=1)
        student_count = result[0]["student_count"] if result else 0
        
        logger.info(
            f"📊 Misconception frequency check: '{misconception_text[:50]}...' "
            f"found in {student_count} students (threshold: {frequency_threshold})"
        )
        
        # Check frequency threshold
        if student_count < frequency_threshold:
            return {
                "promoted": False,
                "reason": "insufficient_frequency",
                "student_count": student_count,
                "threshold": frequency_threshold
            }
        
        # Step 3: Promote to global database
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[{
                "subject": domain,
                "topic": topic,
                "misconception_text": misconception_text,
                "frequency": student_count,
                "source": "student_discovered",
                "added_date": datetime.utcnow().isoformat(),
                "novelty_score": 1.0 - max_similarity  # Higher = more novel
            }],
            documents=[misconception_text]
        )
        
        logger.info(
            f"🎉 PROMOTED TO GLOBAL KB: '{misconception_text}' "
            f"(students={student_count}, novelty={1.0-max_similarity:.2f})"
        )
        
        return {
            "promoted": True,
            "student_count": student_count,
            "novelty_score": 1.0 - max_similarity,
            "doc_id": doc_id
        }
        
    except Exception as e:
        logger.error(f"Error in misconception promotion check: {e}", exc_info=True)
        return {
            "promoted": False,
            "reason": "error",
            "error": str(e)
        }


async def add_misconception_to_global_database(
    misconception_text: str,
    topic: str,
    frequency: int = 1
) -> bool:
    """
    DEPRECATED: Use check_and_promote_misconception_to_global() instead.
    
    This function is kept for backwards compatibility but should not be used
    as it bypasses frequency and novelty checks.
    """
    logger.warning(
        "⚠️ DEPRECATED: add_misconception_to_global_database() called. "
        "Use check_and_promote_misconception_to_global() for proper promotion logic."
    )
    try:
        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection(name="misconceptions")
        
        # Create embedding
        embedder = get_embedder()
        embedding = embedder.encode(misconception_text).tolist()
        
        # Check if already exists (simple check by text)
        existing = collection.get(
            where={"misconception_text": misconception_text}
        )
        
        if existing and existing['ids']:
            logger.info(f"Misconception already exists in global DB: '{misconception_text}'")
            return True
        
        # Add to ChromaDB
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[{
                "topic": topic,
                "misconception_text": misconception_text,
                "frequency": frequency,
                "source": "student_discovered",
                "added_date": datetime.utcnow().isoformat()
            }],
            documents=[misconception_text]
        )
        
        logger.info(f"✅ Added misconception to global database: '{misconception_text}'")
        return True
        
    except Exception as e:
        logger.error(f"Error adding to global misconception database: {e}", exc_info=True)
        return False


async def get_user_personal_misconceptions(
    db: Any,  # MongoDB database
    user_id: str,
    topic: Optional[str] = None,
    only_unresolved: bool = True
) -> List[PersonalMisconception]:
    """
    Retrieve a user's personal misconceptions.
    
    Args:
        db: MongoDB database
        user_id: User's ID
        topic: Optional topic filter
        only_unresolved: If True, only return unresolved misconceptions
        
    Returns:
        List of PersonalMisconception objects
    """
    try:
        users_collection = db.get_collection("users")
        user = await users_collection.find_one({"_id": user_id})
        
        if not user:
            return []
        
        personal_misconceptions = user.get("personal_misconceptions", {})
        
        result = []
        
        if topic:
            # Get misconceptions for specific topic
            topic_misconceptions = personal_misconceptions.get(topic, [])
            for mc_dict in topic_misconceptions:
                mc = PersonalMisconception(**mc_dict)
                if not only_unresolved or not mc.resolved:
                    result.append(mc)
        else:
            # Get all misconceptions across all topics
            for topic_name, misconceptions in personal_misconceptions.items():
                for mc_dict in misconceptions:
                    mc = PersonalMisconception(**mc_dict)
                    if not only_unresolved or not mc.resolved:
                        result.append(mc)
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving personal misconceptions: {e}", exc_info=True)
        return []


async def update_misconception_resolution_status(
    db: Any,  # MongoDB database
    user_id: str,
    topic: str,
    misconception_id: str,
    was_correct: bool,
    threshold: int = 3
) -> bool:
    """
    Update the resolution status of a misconception based on quiz performance.
    
    If student answers correctly 'threshold' times in a row, mark as resolved.
    If they get it wrong, reset streak to 0.
    
    Args:
        db: MongoDB database
        user_id: User's ID
        topic: Topic name
        misconception_id: Misconception ID
        was_correct: Whether student answered correctly
        threshold: Number of correct answers needed to mark as resolved
        
    Returns:
        True if misconception was marked as resolved, False otherwise
    """
    try:
        users_collection = db.get_collection("users")
        
        if was_correct:
            # Increment correct streak
            result = await users_collection.find_one_and_update(
                {
                    "_id": user_id,
                    f"personal_misconceptions.{topic}.misconception_id": misconception_id
                },
                {
                    "$inc": {f"personal_misconceptions.{topic}.$.correct_streak": 1}
                },
                return_document=True
            )
            
            if result:
                # Check if threshold reached
                topic_misconceptions = result.get("personal_misconceptions", {}).get(topic, [])
                for mc in topic_misconceptions:
                    if mc.get("misconception_id") == misconception_id:
                        if mc.get("correct_streak", 0) >= threshold:
                            # Mark as resolved!
                            await users_collection.update_one(
                                {
                                    "_id": user_id,
                                    f"personal_misconceptions.{topic}.misconception_id": misconception_id
                                },
                                {
                                    "$set": {
                                        f"personal_misconceptions.{topic}.$.resolved": True,
                                        f"personal_misconceptions.{topic}.$.resolution_date": datetime.utcnow().isoformat()
                                    }
                                }
                            )
                            logger.info(f"🎉 Misconception RESOLVED for user {user_id}: '{mc.get('misconception_text')}'")
                            return True
        else:
            # Reset correct streak
            await users_collection.update_one(
                {
                    "_id": user_id,
                    f"personal_misconceptions.{topic}.misconception_id": misconception_id
                },
                {
                    "$set": {
                        f"personal_misconceptions.{topic}.$.correct_streak": 0,
                        f"personal_misconceptions.{topic}.$.resolved": False
                    }
                }
            )
            logger.info(f"Reset correct streak for misconception {misconception_id}")
        
        return False
        
    except Exception as e:
        logger.error(f"Error updating misconception resolution: {e}", exc_info=True)
        return False

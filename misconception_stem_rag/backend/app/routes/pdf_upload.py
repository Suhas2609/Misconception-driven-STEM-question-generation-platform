"""Modern PDF upload routes with GPT-4o topic extraction."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from ..db.mongo import get_collection
from ..models.session import LearningSession
from ..models.user import UserModel
from ..routes.auth import get_current_user
from ..services import pdf as pdf_service
from ..services.topic_extraction import extract_topics_from_text
from ..services.topic_question_generation import generate_questions_for_topics
from ..services.explanation_generation import generate_personalized_explanation

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateQuestionsRequest(BaseModel):
    """Request payload for question generation from topics."""
    session_id: str
    selected_topics: list[str]  # List of topic titles
    num_questions_per_topic: int = 2


class QuizSubmission(BaseModel):
    """Request payload for quiz submission."""
    session_id: str
    responses: list[dict]  # List of {question_id, selected_answer, confidence, reasoning}


def _sessions_collection():
    return get_collection("sessions")


@router.get("/sessions")
async def get_user_sessions(
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """
    Get all learning sessions for the current user.
    Returns sessions sorted by creation date (newest first).
    """
    try:
        logger.info(f"📚 Fetching sessions for user: {current_user.id}")
        
        # Find all sessions for this user
        sessions_cursor = sessions_collection.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1)  # Newest first
        
        sessions_list = []
        # Use async for with AsyncIOMotorCursor
        async for session_doc in sessions_cursor:
            # Convert ObjectId to string
            session_doc["_id"] = str(session_doc["_id"])
            
            # Calculate summary stats if quiz was completed
            quiz_results = session_doc.get("quiz_results", {})
            session_summary = {
                "id": session_doc.get("id"),
                "filename": session_doc.get("filename"),
                "created_at": session_doc.get("created_at"),
                "topics_count": len(session_doc.get("topics", [])),
                "selected_topics_count": len(session_doc.get("selected_topics", [])),
                "questions_count": len(session_doc.get("generated_questions", [])),
                "quiz_completed": bool(quiz_results),
                "score_percentage": quiz_results.get("score_percentage"),
                "total_questions": quiz_results.get("total_questions"),
                "correct_count": quiz_results.get("correct_count"),
                "avg_confidence": quiz_results.get("avg_confidence"),
                "topics": session_doc.get("selected_topics", []),
                "submitted_at": quiz_results.get("submitted_at"),
            }
            sessions_list.append(session_summary)
        
        logger.info(f"✅ Found {len(sessions_list)} sessions for user")
        return {"sessions": sessions_list}
        
    except Exception as e:
        logger.error(f"❌ Error fetching sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """
    Get detailed information about a specific session, including quiz feedback.
    """
    try:
        logger.info(f"🔍 Fetching session detail: {session_id}")
        
        session = sessions_collection.find_one({"id": session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify ownership
        if session.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
        
        # Convert ObjectId to string
        session["_id"] = str(session["_id"])
        
        logger.info(f"✅ Session retrieved successfully")
        return {"session": session}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching session detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session: {str(e)}"
        )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf_with_topic_extraction(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """
    Upload a PDF, extract text, use GPT-4o to identify topics, and create a learning session.
    
    Flow:
    1. Save uploaded PDF to disk
    2. Extract text chunks from PDF
    3. Call GPT-4o to extract structured topics (core prompt!)
    4. Create a LearningSession in MongoDB
    5. Return session ID + extracted topics for frontend display
    """
    logger.info(f"📥 PDF upload from user {current_user.email}: {file.filename}")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file
    destination_dir = Path("data/pdfs")
    destination_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unique filename to avoid conflicts
    file_id = str(uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    file_path = destination_dir / safe_filename
    
    try:
        contents = await file.read()
        file_path.write_bytes(contents)
        logger.info(f"💾 Saved PDF to {file_path} ({len(contents)} bytes)")
    except Exception as e:
        logger.error(f"❌ Failed to save PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Extract text from PDF
    try:
        logger.info(f"📄 Extracting text from PDF...")
        chunks = pdf_service.process_pdf(str(file_path))
        logger.info(f"✅ Extracted {len(chunks)} text chunks")
    except Exception as e:
        logger.error(f"❌ PDF processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )
    
    if not chunks:
        logger.warning("⚠️ No text extracted from PDF")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from PDF. File may be empty or image-based."
        )
    
    # Combine chunks for topic extraction (GPT-4o can handle large context)
    full_text = "\n\n".join(chunks)
    
    # **CORE PROMPT: Extract topics using GPT-4o**
    try:
        logger.info(f"🧠 Calling GPT-4o for topic extraction...")
        topic_result = extract_topics_from_text(full_text, file.filename)
        logger.info(f"✅ Extracted {len(topic_result.topics)} topics")
    except Exception as e:
        logger.error(f"❌ Topic extraction failed: {e}")
        # Don't fail the upload - just return empty topics
        topic_result = None
    
    # Create learning session
    session_id = f"sess_{uuid4()}"
    
    session = LearningSession(
        id=session_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        topics=[t.model_dump() for t in topic_result.topics] if topic_result else [],
        document_summary=topic_result.document_summary if topic_result else None,
        recommended_order=topic_result.recommended_order if topic_result else [],
        num_chunks=len(chunks),
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow(),
        status="active"
    )
    
    # Save to MongoDB
    try:
        session_doc = session.model_dump()
        session_doc["_id"] = session_id
        await sessions_collection.insert_one(session_doc)
        logger.info(f"💾 Created session {session_id} for user {current_user.email}")
    except Exception as e:
        logger.error(f"❌ Failed to save session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create learning session"
        )
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "num_chunks": len(chunks),
        "topics": [t.model_dump() for t in topic_result.topics] if topic_result else [],
        "document_summary": topic_result.document_summary if topic_result else None,
        "recommended_order": topic_result.recommended_order if topic_result else [],
        "message": f"Successfully extracted {len(topic_result.topics) if topic_result else 0} topics"
    }


@router.get("/sessions")
async def get_user_sessions(
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """Get all learning sessions for the current user."""
    try:
        cursor = sessions_collection.find({"user_id": current_user.id})
        sessions = await cursor.to_list(length=100)
        
        # Convert _id to id for consistency
        for session in sessions:
            if "_id" in session:
                session["id"] = session["_id"]
                del session["_id"]
        
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"❌ Failed to fetch sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """Get details of a specific learning session."""
    try:
        session = await sessions_collection.find_one({"_id": session_id, "user_id": current_user.id})
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Convert _id to id
        session["id"] = session["_id"]
        del session["_id"]
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.patch("/sessions/{session_id}/select-topics")
async def select_topics_for_practice(
    session_id: str,
    selected_topics: list[str],
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """
    Update session with user's selected topics for quiz generation.
    This is called after user reviews extracted topics and chooses which ones to practice.
    """
    try:
        result = await sessions_collection.update_one(
            {"_id": session_id, "user_id": current_user.id},
            {
                "$set": {
                    "selected_topics": selected_topics,
                    "last_accessed": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"✅ User {current_user.email} selected {len(selected_topics)} topics for session {session_id}")
        
        return {
            "session_id": session_id,
            "selected_topics": selected_topics,
            "message": f"Selected {len(selected_topics)} topics for practice"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update session topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update topic selection"
        )


@router.post("/sessions/{session_id}/generate-questions")
async def generate_questions_from_topics(
    session_id: str,
    payload: GenerateQuestionsRequest,
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """
    Generate personalized questions using GPT-4o based on:
    - Selected topics (from topic extraction)
    - User's cognitive profile (from assessment)
    - PDF content (RAG retrieval)
    
    This is the CORE QUESTION GENERATION endpoint with full prompt engineering!
    """
    logger.info(f"🎯 Generating questions for session {session_id} - {len(payload.selected_topics)} topics")
    
    try:
        # 1. Fetch session data
        session = await sessions_collection.find_one({"_id": session_id, "user_id": current_user.id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # 2. Get user's cognitive traits
        cognitive_traits = current_user.cognitive_traits
        # Convert Pydantic model to dict if necessary
        if hasattr(cognitive_traits, 'model_dump'):
            cognitive_traits = cognitive_traits.model_dump()
        elif hasattr(cognitive_traits, 'dict'):
            cognitive_traits = cognitive_traits.dict()
        elif not isinstance(cognitive_traits, dict):
            cognitive_traits = {}
        
        logger.info(f"📊 User cognitive profile: {cognitive_traits}")
        
        # 3. Filter selected topics
        all_topics = session.get("topics", [])
        selected_topic_objects = [
            topic for topic in all_topics 
            if topic.get("title") in payload.selected_topics
        ]
        
        if not selected_topic_objects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid topics found for generation"
            )
        
        # 4. Get PDF content for RAG
        pdf_path = session.get("file_path")  # Fixed: was "pdf_path", should be "file_path"
        logger.info(f"📁 PDF path from session: {pdf_path}")
        
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file path not found in session"
            )
        
        if not Path(pdf_path).exists():
            logger.error(f"❌ PDF file does not exist at: {pdf_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDF file not found at path: {pdf_path}"
            )
        
        # Extract text from PDF
        chunks = pdf_service.process_pdf(pdf_path)
        pdf_content = " ".join(chunks[:10])  # Use first 10 chunks for context
        
        logger.info(f"📄 Using {len(chunks)} PDF chunks for context")
        
        # 5. **CORE PROMPT ENGINEERING** - Generate questions with GPT-4o
        questions = generate_questions_for_topics(
            topics=selected_topic_objects,
            pdf_content=pdf_content,
            cognitive_traits=cognitive_traits,
            num_questions_per_topic=payload.num_questions_per_topic
        )
        
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate questions - GPT-4o did not return valid questions"
            )
        
        # 6. Save generated questions to session
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "generated_questions": questions,
                    "questions_generated_at": datetime.utcnow(),
                    "num_questions": len(questions)
                }
            }
        )
        
        logger.info(f"✅ Generated {len(questions)} personalized questions!")
        
        return {
            "session_id": session_id,
            "questions": questions,
            "num_questions": len(questions),
            "topics_covered": [topic["title"] for topic in selected_topic_objects]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Question generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question generation failed: {str(e)}"
        )


@router.post("/sessions/{session_id}/submit-quiz")
async def submit_quiz_with_feedback(
    session_id: str,
    payload: QuizSubmission,
    current_user: UserModel = Depends(get_current_user),
    sessions_collection=Depends(_sessions_collection),
):
    """
    Submit quiz responses and get personalized feedback using GPT-4o.
    
    This is GPT-4o PROMPT #3: Generate personalized explanations for each answer
    - Analyzes correctness
    - Identifies misconceptions
    - Provides tailored feedback based on cognitive profile
    - Updates user's cognitive traits based on performance
    """
    logger.info(f"📝 Quiz submission for session {session_id} - {len(payload.responses)} responses")
    
    try:
        # 1. Fetch session with questions
        session = await sessions_collection.find_one({"_id": session_id, "user_id": current_user.id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        generated_questions = session.get("generated_questions", [])
        if not generated_questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No questions found in this session"
            )
        
        # 2. Get user's cognitive traits
        cognitive_traits = current_user.cognitive_traits
        if hasattr(cognitive_traits, 'model_dump'):
            cognitive_traits = cognitive_traits.model_dump()
        elif hasattr(cognitive_traits, 'dict'):
            cognitive_traits = cognitive_traits.dict()
        elif not isinstance(cognitive_traits, dict):
            cognitive_traits = {}
        
        # 3. Process each response and generate explanations
        feedback_results = []
        correct_count = 0
        total_confidence = 0
        
        for response in payload.responses:
            question_num = response.get("question_number")
            selected_answer = response.get("selected_answer")
            confidence = response.get("confidence", 0.5)
            reasoning = response.get("reasoning")
            
            # Find the question
            question = None
            for q in generated_questions:
                if q.get("question_number") == question_num:
                    question = q
                    break
            
            if not question:
                logger.warning(f"Question {question_num} not found in session")
                continue
            
            # Check if answer is correct
            is_correct = False
            for option in question.get("options", []):
                if option.get("text") == selected_answer and option.get("type") == "correct":
                    is_correct = True
                    break
            
            if is_correct:
                correct_count += 1
            total_confidence += confidence
            
            # **CORE GPT-4o PROMPT #3** - Generate personalized explanation
            explanation = generate_personalized_explanation(
                question=question,
                user_answer=selected_answer,
                is_correct=is_correct,
                confidence=confidence,
                reasoning=reasoning,
                cognitive_traits=cognitive_traits
            )
            
            feedback_results.append({
                "question_number": question_num,
                "question_stem": question.get("stem"),
                "selected_answer": selected_answer,
                "is_correct": is_correct,
                "confidence": confidence,
                "explanation": explanation.get("explanation"),
                "misconception_addressed": explanation.get("misconception_addressed"),
                "confidence_analysis": explanation.get("confidence_analysis"),
                "learning_tips": explanation.get("learning_tips"),
                "encouragement": explanation.get("encouragement")
            })
        
        # 4. Calculate performance metrics
        total_questions = len(payload.responses)
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        avg_confidence = (total_confidence / total_questions) if total_questions > 0 else 0
        
        # 5. Update cognitive traits based on performance
        # Simple trait adjustment - can be enhanced with more sophisticated analysis
        trait_adjustments = {}
        
        if score_percentage >= 80:
            # Strong performance - boost traits slightly
            for trait, value in cognitive_traits.items():
                current_val = float(value) if isinstance(value, (int, float)) else 0.5
                trait_adjustments[trait] = min(1.0, current_val + 0.02)
        elif score_percentage < 50:
            # Needs support - slight decrease to trigger easier questions next time
            for trait, value in cognitive_traits.items():
                current_val = float(value) if isinstance(value, (int, float)) else 0.5
                trait_adjustments[trait] = max(0.0, current_val - 0.02)
        else:
            # Maintain current traits
            trait_adjustments = cognitive_traits
        
        # 6. Save quiz results to session
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "quiz_submitted_at": datetime.utcnow(),
                    "quiz_results": {
                        "score_percentage": score_percentage,
                        "correct_count": correct_count,
                        "total_questions": total_questions,
                        "avg_confidence": avg_confidence,
                        "responses": feedback_results
                    }
                }
            }
        )
        
        # 7. Update user's cognitive traits
        users_collection = get_collection("users")
        await users_collection.update_one(
            {"_id": current_user.id},
            {"$set": {"cognitive_traits": trait_adjustments}}
        )
        
        logger.info(f"✅ Quiz graded: {correct_count}/{total_questions} correct ({score_percentage:.1f}%)")
        
        return {
            "session_id": session_id,
            "score_percentage": score_percentage,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "avg_confidence": avg_confidence,
            "feedback": feedback_results,
            "updated_traits": trait_adjustments,
            "message": f"Quiz complete! You scored {score_percentage:.1f}%"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Quiz submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz submission failed: {str(e)}"
        )

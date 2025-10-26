"""Learning session model for tracking user study sessions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LearningSession(BaseModel):
    """Tracks a user's learning session with uploaded material."""

    id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="User who created this session")
    filename: str = Field(description="Original PDF filename")
    file_path: str | None = Field(default=None, description="Storage path of uploaded file")
    
    # Topic extraction results
    topics: list[dict[str, Any]] = Field(default_factory=list, description="Extracted topics from GPT-4o")
    document_summary: str | None = Field(default=None, description="AI-generated document summary")
    recommended_order: list[str] = Field(default_factory=list, description="Suggested learning sequence")
    
    # User selections
    selected_topics: list[str] = Field(default_factory=list, description="Topics user chose to practice")
    
    # Session metadata
    num_chunks: int = Field(default=0, description="Number of text chunks extracted")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    # Progress tracking
    questions_generated: int = Field(default=0, description="Total questions created for this session")
    questions_answered: int = Field(default=0, description="Questions user has attempted")
    average_score: float | None = Field(default=None, description="Average score across attempts")
    
    # Status
    status: str = Field(default="active", description="active | paused | completed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "sess_abc123",
                "user_id": "user@example.com",
                "filename": "physics_kinematics.pdf",
                "topics": [
                    {
                        "title": "Newton's Laws of Motion",
                        "difficulty": "medium",
                        "subject_area": "physics"
                    }
                ],
                "selected_topics": ["Newton's Laws of Motion"],
                "created_at": "2025-10-26T12:00:00Z",
                "status": "active"
            }
        }

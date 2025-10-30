"""
Misconception Models for Student Misconception Tracking
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PersonalMisconception(BaseModel):
    """
    Represents a misconception discovered from a student's quiz responses.
    
    This model tracks individual misconceptions that a student has demonstrated,
    allowing the system to generate targeted remedial questions.
    """
    misconception_id: str = Field(
        ...,
        description="Unique identifier for this misconception instance"
    )
    misconception_text: str = Field(
        ...,
        description="The actual misconception text (e.g., 'Confuses checked vs unchecked exceptions')"
    )
    topic: str = Field(
        ...,
        description="Topic where this misconception was observed"
    )
    question_context: Optional[str] = Field(
        None,
        description="Original question that revealed this misconception"
    )
    student_reasoning: Optional[str] = Field(
        None,
        description="Student's reasoning that revealed the misconception"
    )
    first_encountered: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this misconception was first observed"
    )
    frequency: int = Field(
        default=1,
        description="Number of times student has made this same mistake"
    )
    last_occurrence: datetime = Field(
        default_factory=datetime.utcnow,
        description="Most recent time this misconception was observed"
    )
    resolved: bool = Field(
        default=False,
        description="Whether student has overcome this misconception"
    )
    resolution_date: Optional[datetime] = Field(
        None,
        description="When this misconception was marked as resolved"
    )
    correct_streak: int = Field(
        default=0,
        description="Number of consecutive correct answers on this misconception"
    )
    targeted_question_count: int = Field(
        default=0,
        description="Number of questions generated to address this misconception"
    )
    severity: str = Field(
        default="medium",
        description="Severity level: low, medium, high, critical"
    )
    related_trait: Optional[str] = Field(
        None,
        description="Cognitive trait most affected by this misconception"
    )


class DiscoveredMisconception(BaseModel):
    """
    Represents a newly discovered misconception from quiz analysis.
    
    This is the intermediate model used during misconception extraction
    before it's stored in the user's personal misconception history.
    """
    misconception_text: str
    topic: str
    confidence: float = Field(
        default=0.8,
        description="AI confidence in this misconception identification (0.0-1.0)"
    )
    evidence: str = Field(
        ...,
        description="Evidence that led to this misconception identification"
    )
    severity: str = Field(
        default="medium",
        description="Estimated severity: low, medium, high, critical"
    )
    related_trait: Optional[str] = None
    suggested_remediation: Optional[str] = None


class MisconceptionProgress(BaseModel):
    """
    Tracks overall misconception resolution progress for a topic.
    """
    topic: str
    total_misconceptions: int = 0
    resolved_misconceptions: int = 0
    active_misconceptions: int = 0
    resolution_rate: float = Field(
        default=0.0,
        description="Percentage of misconceptions resolved (0.0-1.0)"
    )
    average_resolution_time_days: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class MisconceptionResolutionEvent(BaseModel):
    """
    Records an event where a student answered correctly on a previously-wrong misconception.
    """
    misconception_id: str
    question_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    was_correct: bool
    reasoning_quality: Optional[float] = None

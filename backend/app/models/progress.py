"""
Progress Models
Models for quiz progress tracking and submission.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class AnswerRecord(BaseModel):
    """Individual answer record."""
    question_index: int = Field(..., description="Question index in the quiz")
    question_id: Optional[str] = Field(None, description="Question UUID if available")
    question_text: str = Field(..., description="The question text")
    selected: str = Field(..., description="User's selected answer")
    correct: str = Field(..., description="Correct answer")
    is_correct: bool = Field(..., description="Whether answer was correct")


class SubmitQuizRequest(BaseModel):
    """Request model for submitting quiz results."""
    user_id: str = Field(..., min_length=1, description="User identifier")
    topic: str = Field(..., min_length=1, description="Course topic")
    difficulty: str = Field(..., description="Course difficulty level")
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_title: str = Field(..., min_length=1, description="Chapter title")
    answers: List[AnswerRecord] = Field(..., description="List of answer records")
    total_questions: int = Field(..., ge=1, description="Total questions in quiz")
    correct_count: int = Field(..., ge=0, description="Number of correct answers")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "topic": "Python Programming",
                "difficulty": "intermediate",
                "chapter_number": 1,
                "chapter_title": "Python Basics",
                "answers": [
                    {
                        "question_index": 0,
                        "question_id": "q1",
                        "question_text": "What is Python?",
                        "selected": "A",
                        "correct": "A",
                        "is_correct": True
                    }
                ],
                "total_questions": 10,
                "correct_count": 8
            }
        }


class ProgressResponse(BaseModel):
    """Response model for a single progress record."""
    user_id: str
    course_topic: str
    difficulty: str
    chapter_number: int
    chapter_title: str
    score: float = Field(..., ge=0, le=1, description="Score as decimal (0-1)")
    score_percent: int = Field(..., ge=0, le=100, description="Score as percentage")
    correct_answers: int
    total_questions: int
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ProgressListResponse(BaseModel):
    """Response model for list of progress records."""
    user_id: str
    total_quizzes: int
    progress: List[ProgressResponse]


class ProgressSummary(BaseModel):
    """Summary of user's overall progress."""
    user_id: str
    total_quizzes_completed: int
    total_questions_answered: int
    total_correct: int
    average_score: float
    courses: List[str]

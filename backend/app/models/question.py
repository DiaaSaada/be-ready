"""
Pydantic models for question generation system.
Defines MCQ and True/False question structures, generation configs, and API models.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, computed_field
import uuid


class QuestionType(str, Enum):
    """Types of questions supported by the system."""
    MCQ = "mcq"
    TRUE_FALSE = "true_false"


class QuestionDifficulty(str, Enum):
    """Difficulty levels for individual questions."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MCQQuestion(BaseModel):
    """Multiple Choice Question model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique question identifier")
    type: QuestionType = Field(default=QuestionType.MCQ, description="Question type")
    difficulty: QuestionDifficulty = Field(..., description="Question difficulty level")
    question_text: str = Field(..., min_length=10, description="The question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Four answer options (A, B, C, D)")
    correct_answer: str = Field(..., pattern=r"^[A-D]$", description="Correct answer letter (A, B, C, or D)")
    explanation: str = Field(..., min_length=10, description="Explanation of the correct answer")
    points: int = Field(default=1, ge=1, description="Points awarded for correct answer")

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        if len(v) != 4:
            raise ValueError("MCQ must have exactly 4 options")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "mcq",
                "difficulty": "medium",
                "question_text": "What is the primary purpose of a project charter?",
                "options": [
                    "A) To define the project budget",
                    "B) To formally authorize the project and document requirements",
                    "C) To assign team members to tasks",
                    "D) To track project progress"
                ],
                "correct_answer": "B",
                "explanation": "A project charter formally authorizes the project, names the project manager, and documents initial requirements and stakeholder expectations.",
                "points": 1
            }
        }


class TrueFalseQuestion(BaseModel):
    """True/False Question model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique question identifier")
    type: QuestionType = Field(default=QuestionType.TRUE_FALSE, description="Question type")
    difficulty: QuestionDifficulty = Field(..., description="Question difficulty level")
    question_text: str = Field(..., min_length=10, description="The statement to evaluate")
    correct_answer: bool = Field(..., description="True or False")
    explanation: str = Field(..., min_length=10, description="Explanation of why the statement is true or false")
    points: int = Field(default=1, ge=1, description="Points awarded for correct answer")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "type": "true_false",
                "difficulty": "easy",
                "question_text": "A project manager is responsible for defining the project scope.",
                "correct_answer": True,
                "explanation": "True. The project manager works with stakeholders to define and document the project scope, which includes deliverables, boundaries, and acceptance criteria.",
                "points": 1
            }
        }


class ChapterQuestions(BaseModel):
    """Collection of questions for a specific chapter."""
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_title: str = Field(..., description="Title of the chapter")
    mcq_questions: List[MCQQuestion] = Field(default_factory=list, description="List of MCQ questions")
    true_false_questions: List[TrueFalseQuestion] = Field(default_factory=list, description="List of True/False questions")

    @computed_field
    @property
    def total_questions(self) -> int:
        """Total number of questions in this chapter."""
        return len(self.mcq_questions) + len(self.true_false_questions)

    @computed_field
    @property
    def total_points(self) -> int:
        """Total points available in this chapter."""
        mcq_points = sum(q.points for q in self.mcq_questions)
        tf_points = sum(q.points for q in self.true_false_questions)
        return mcq_points + tf_points

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "chapter_title": "Introduction to Project Management",
                "mcq_questions": [],
                "true_false_questions": [],
                "total_questions": 8,
                "total_points": 8
            }
        }


class QuestionGenerationConfig(BaseModel):
    """Configuration for generating questions for a chapter."""
    topic: str = Field(..., description="Course topic")
    difficulty: str = Field(..., description="Course difficulty level")
    audience: str = Field(..., description="Target audience description")
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_title: str = Field(..., description="Chapter title")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts to test")
    key_ideas: List[str] = Field(default_factory=list, description="Specific testable ideas from content")
    recommended_mcq_count: int = Field(default=5, ge=1, le=40, description="Number of MCQ questions to generate")
    recommended_tf_count: int = Field(default=3, ge=1, le=15, description="Number of True/False questions to generate")

    @classmethod
    def derive_audience(cls, difficulty: str) -> str:
        """Derive target audience from difficulty level."""
        audience_map = {
            "beginner": "beginners, kids, or teens with no prior knowledge",
            "intermediate": "college students or professionals with some background",
            "advanced": "professionals or experts seeking deep understanding"
        }
        return audience_map.get(difficulty, "general learners")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Project Management",
                "difficulty": "intermediate",
                "audience": "college students or professionals with some background",
                "chapter_number": 1,
                "chapter_title": "Introduction to Project Management",
                "key_concepts": ["Project lifecycle", "Stakeholder management", "Resource allocation"],
                "recommended_mcq_count": 5,
                "recommended_tf_count": 3
            }
        }


class GenerateQuestionsRequest(BaseModel):
    """Request model for generating questions for a chapter."""
    course_id: Optional[str] = Field(default=None, description="Course ID from database (optional if providing chapter details)")
    chapter_number: int = Field(..., ge=1, description="Chapter number to generate questions for")
    override_mcq_count: Optional[int] = Field(default=None, ge=1, le=20, description="Override default MCQ count")
    override_tf_count: Optional[int] = Field(default=None, ge=1, le=10, description="Override default True/False count")

    class Config:
        json_schema_extra = {
            "example": {
                "course_id": "507f1f77bcf86cd799439011",
                "chapter_number": 1,
                "override_mcq_count": 10,
                "override_tf_count": 5
            }
        }


class GenerateQuestionsResponse(BaseModel):
    """Response model for question generation."""
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_title: str = Field(..., description="Chapter title")
    questions: ChapterQuestions = Field(..., description="Generated questions")
    generation_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generation metadata (model used, tokens, timing, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "chapter_title": "Introduction to Project Management",
                "questions": {
                    "chapter_number": 1,
                    "chapter_title": "Introduction to Project Management",
                    "mcq_questions": [],
                    "true_false_questions": [],
                    "total_questions": 8,
                    "total_points": 8
                },
                "generation_info": {
                    "model": "claude-sonnet-4-20250514",
                    "input_tokens": 1500,
                    "output_tokens": 2000,
                    "generation_time_ms": 3500
                }
            }
        }

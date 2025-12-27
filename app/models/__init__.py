"""
Pydantic models for the AI Learning Platform.
"""
from app.models.course import (
    GenerateCourseRequest,
    GenerateCourseResponse,
    Chapter,
    CourseConfig,
)
from app.models.validation import (
    TopicValidationRequest,
    TopicValidationResult,
    TopicComplexity,
)
from app.models.question import (
    QuestionType,
    QuestionDifficulty,
    MCQQuestion,
    TrueFalseQuestion,
    ChapterQuestions,
    QuestionGenerationConfig,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
)

__all__ = [
    # Course models
    "GenerateCourseRequest",
    "GenerateCourseResponse",
    "Chapter",
    "CourseConfig",
    # Validation models
    "TopicValidationRequest",
    "TopicValidationResult",
    "TopicComplexity",
    # Question models
    "QuestionType",
    "QuestionDifficulty",
    "MCQQuestion",
    "TrueFalseQuestion",
    "ChapterQuestions",
    "QuestionGenerationConfig",
    "GenerateQuestionsRequest",
    "GenerateQuestionsResponse",
]

"""
Pydantic models for topic validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class TopicComplexity(BaseModel):
    """Complexity assessment for a topic."""
    score: int = Field(..., ge=1, le=10, description="Complexity score from 1-10")
    level: Literal["basic", "intermediate", "advanced", "expert"] = Field(
        ...,
        description="Complexity level category"
    )
    estimated_chapters: int = Field(..., ge=1, description="Estimated number of chapters")
    estimated_hours: float = Field(..., gt=0, description="Estimated study hours")
    reasoning: str = Field(..., description="Explanation of complexity assessment")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 6,
                "level": "intermediate",
                "estimated_chapters": 5,
                "estimated_hours": 15.0,
                "reasoning": "This topic covers moderate depth with several interconnected concepts."
            }
        }


class TopicValidationResult(BaseModel):
    """Result of topic validation."""
    status: Literal["accepted", "rejected", "needs_clarification"] = Field(
        ...,
        description="Validation status"
    )
    topic: str = Field(..., description="Original topic as provided")
    normalized_topic: str = Field(..., description="Cleaned/normalized version of the topic")
    reason: Optional[Literal["too_broad", "too_narrow", "unclear", "inappropriate"]] = Field(
        default=None,
        description="Reason for rejection or clarification needed"
    )
    message: str = Field(..., description="Human-readable explanation")
    suggestions: List[str] = Field(
        default_factory=list,
        description="Alternative topic suggestions if rejected"
    )
    complexity: Optional[TopicComplexity] = Field(
        default=None,
        description="Complexity assessment (only for accepted topics)"
    )
    is_certification: bool = Field(
        default=False,
        description="Whether the topic is a recognized certification or credential"
    )
    certification_body: Optional[str] = Field(
        default=None,
        description="Name of the certifying organization (e.g., PMI, AWS, CompTIA)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "topic": "Introduction to Machine Learning",
                "normalized_topic": "introduction to machine learning",
                "reason": None,
                "message": "This is a well-scoped topic suitable for a single course.",
                "suggestions": [],
                "complexity": {
                    "score": 7,
                    "level": "intermediate",
                    "estimated_chapters": 6,
                    "estimated_hours": 20.0,
                    "reasoning": "Covers foundational ML concepts with practical applications."
                }
            }
        }


class TopicValidationRequest(BaseModel):
    """Request model for topic validation endpoint."""
    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The topic to validate"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Python Web Development with FastAPI"
            }
        }

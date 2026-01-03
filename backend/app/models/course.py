"""
Pydantic models for API requests and responses.
These define the structure of data we receive and send.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class GenerateCourseRequest(BaseModel):
    """Request model for generating a course from a topic."""
    topic: str = Field(..., min_length=1, max_length=200, description="The topic/subject for the course")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        default="intermediate",
        description="Difficulty level for all chapters: beginner, intermediate, or advanced"
    )
    skip_validation: bool = Field(
        default=False,
        description="Skip topic validation (for testing purposes)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Project Management",
                "difficulty": "intermediate",
                "skip_validation": False
            }
        }


class Chapter(BaseModel):
    """Model representing a single chapter."""
    number: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    summary: str = Field(..., description="Brief summary of the chapter")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts covered")
    difficulty: str = Field(default="intermediate", description="Difficulty level: beginner, intermediate, or advanced")
    estimated_time_minutes: int = Field(default=30, description="Estimated time to complete this chapter in minutes")

    class Config:
        json_schema_extra = {
            "example": {
                "number": 1,
                "title": "Introduction to Project Management",
                "summary": "Learn the fundamentals of project management including key concepts, methodologies, and best practices.",
                "key_concepts": [
                    "Project lifecycle",
                    "Stakeholder management",
                    "Resource allocation"
                ],
                "difficulty": "beginner",
                "estimated_time_minutes": 25
            }
        }


class CourseConfig(BaseModel):
    """Configuration for course structure based on complexity and difficulty."""
    recommended_chapters: int = Field(..., ge=1, le=20, description="Recommended number of chapters")
    estimated_study_hours: float = Field(..., gt=0, description="Total estimated study hours")
    time_per_chapter_minutes: int = Field(..., gt=0, description="Average time per chapter in minutes")
    chapter_depth: Literal["overview", "detailed", "comprehensive"] = Field(
        ...,
        description="Depth of content coverage per chapter"
    )
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        ...,
        description="Course difficulty level"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recommended_chapters": 6,
                "estimated_study_hours": 4.5,
                "time_per_chapter_minutes": 45,
                "chapter_depth": "detailed",
                "difficulty": "intermediate"
            }
        }


class GenerateCourseResponse(BaseModel):
    """Response model for course generation."""
    id: Optional[str] = Field(default=None, description="Course ID (MongoDB ObjectId)")
    topic: str = Field(..., description="The topic of the course")
    difficulty: str = Field(..., description="Course difficulty level")
    category: Optional[str] = Field(default=None, description="Topic category (official_certification, college_course, high_school, etc.)")
    total_chapters: int = Field(..., description="Total number of chapters")
    estimated_study_hours: float = Field(..., description="Total estimated study hours")
    time_per_chapter_minutes: int = Field(..., description="Average time per chapter in minutes")
    complexity_score: Optional[int] = Field(default=None, ge=1, le=10, description="Topic complexity score from validation")
    chapters: List[Chapter] = Field(..., description="List of chapters")
    message: str = Field(default="Course generated successfully", description="Status message")
    config: Optional[CourseConfig] = Field(default=None, description="Course configuration used for generation")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Project Management",
                "difficulty": "intermediate",
                "total_chapters": 6,
                "estimated_study_hours": 4.5,
                "time_per_chapter_minutes": 45,
                "complexity_score": 5,
                "message": "Course generated successfully",
                "chapters": [
                    {
                        "number": 1,
                        "title": "Introduction to Project Management",
                        "summary": "Learn the fundamentals of project management.",
                        "key_concepts": ["Project lifecycle", "Stakeholder management"],
                        "difficulty": "intermediate",
                        "estimated_time_minutes": 45
                    }
                ]
            }
        }
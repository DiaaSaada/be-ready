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
        ...,
        description="Difficulty level for all chapters: beginner, intermediate, or advanced"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Project Management",
                "difficulty": "beginner"
            }
        }


class Chapter(BaseModel):
    """Model representing a single chapter."""
    number: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    summary: str = Field(..., description="Brief summary of the chapter")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts covered")
    difficulty: str = Field(default="intermediate", description="Difficulty level: beginner, intermediate, or advanced")
    
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
                "difficulty": "beginner"
            }
        }


class GenerateCourseResponse(BaseModel):
    """Response model for course generation."""
    topic: str = Field(..., description="The topic of the course")
    total_chapters: int = Field(..., description="Total number of chapters")
    chapters: List[Chapter] = Field(..., description="List of chapters")
    message: str = Field(default="Course generated successfully", description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Project Management",
                "total_chapters": 3,
                "message": "Course generated successfully",
                "chapters": [
                    {
                        "number": 1,
                        "title": "Introduction to Project Management",
                        "summary": "Learn the fundamentals of project management.",
                        "key_concepts": ["Project lifecycle", "Stakeholder management"],
                        "difficulty": "beginner"
                    }
                ]
            }
        }
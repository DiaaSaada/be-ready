"""
Pydantic models for document structure analysis.
These define the structure for the two-phase file-to-course generation flow.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

from .course import FileUploadResult


class DetectedSection(BaseModel):
    """A detected section/chapter in the document."""
    order: int = Field(..., description="Order in the document (1-indexed)")
    title: str = Field(..., description="Detected section title")
    summary: str = Field(..., description="Brief summary of section content")
    key_topics: List[str] = Field(default_factory=list, description="Key topics identified (3-7 per section)")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Detection confidence (0-1)")
    source_file: Optional[str] = Field(default=None, description="Source filename this section came from")

    class Config:
        json_schema_extra = {
            "example": {
                "order": 1,
                "title": "Introduction to Machine Learning",
                "summary": "Covers the fundamentals of ML including supervised and unsupervised learning.",
                "key_topics": ["supervised learning", "unsupervised learning", "model training"],
                "confidence": 0.9,
                "source_file": "ml_textbook.pdf"
            }
        }


class DocumentOutline(BaseModel):
    """Complete document structure analysis result."""
    document_title: str = Field(..., description="Inferred document title")
    document_type: str = Field(
        default="notes",
        description="Type of document: textbook, article, manual, notes, lecture, other"
    )
    total_sections: int = Field(..., ge=1, description="Total number of detected sections")
    sections: List[DetectedSection] = Field(..., description="List of detected sections")
    estimated_total_time_minutes: int = Field(default=60, description="Estimated total study time")
    analysis_notes: Optional[str] = Field(default=None, description="LLM notes about document structure")

    class Config:
        json_schema_extra = {
            "example": {
                "document_title": "Machine Learning Fundamentals",
                "document_type": "textbook",
                "total_sections": 5,
                "sections": [],
                "estimated_total_time_minutes": 180,
                "analysis_notes": "Well-structured textbook with clear chapter divisions."
            }
        }


class DocumentAnalysisResponse(BaseModel):
    """Response with detected document structure for user review."""
    analysis_id: str = Field(..., description="Temporary ID to reference this analysis")
    document_outline: DocumentOutline = Field(..., description="Detected document structure")
    source_files: List[FileUploadResult] = Field(..., description="Results of file processing")
    extracted_text_chars: int = Field(..., description="Total characters extracted from files")
    expires_at: datetime = Field(..., description="When this analysis will expire")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "abc123",
                "document_outline": {},
                "source_files": [],
                "extracted_text_chars": 15000,
                "expires_at": "2025-01-03T12:30:00Z"
            }
        }


class ConfirmedSection(BaseModel):
    """A section confirmed/edited by the user."""
    order: int = Field(..., description="Section order (user may have reordered)")
    title: str = Field(..., description="Section title (user may have edited)")
    include: bool = Field(default=True, description="Whether to include this section in the course")
    key_topics: List[str] = Field(default_factory=list, description="Key topics (user may have edited)")

    class Config:
        json_schema_extra = {
            "example": {
                "order": 1,
                "title": "Introduction to Machine Learning",
                "include": True,
                "key_topics": ["supervised learning", "unsupervised learning"]
            }
        }


class ConfirmOutlineRequest(BaseModel):
    """Request to confirm outline and generate chapters."""
    analysis_id: str = Field(..., description="ID of the pending analysis")
    confirmed_sections: List[ConfirmedSection] = Field(..., description="User-confirmed sections")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        default="intermediate",
        description="Difficulty level for the course"
    )
    custom_topic: Optional[str] = Field(
        default=None,
        description="Override the detected document title as course topic"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "abc123",
                "confirmed_sections": [
                    {
                        "order": 1,
                        "title": "Introduction",
                        "include": True,
                        "key_topics": ["basics", "overview"]
                    }
                ],
                "difficulty": "intermediate",
                "custom_topic": None
            }
        }

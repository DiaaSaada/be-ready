"""Token usage tracking models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OperationType(str, Enum):
    """Types of AI operations that consume tokens."""
    TOPIC_VALIDATION = "TOPIC_VALIDATION"
    ANALYZE_DOCUMENT = "ANALYZE_DOCUMENT"
    CHAPTER_GENERATION = "CHAPTER_GENERATION"
    QUESTION_GENERATION = "QUESTION_GENERATION"
    ANSWER_CHECK = "ANSWER_CHECK"
    FEEDBACK_GENERATION = "FEEDBACK_GENERATION"
    RAG_ANSWER = "RAG_ANSWER"


class TokenUsageRecord(BaseModel):
    """Record of token usage for a single AI operation."""
    user_id: str = Field(..., description="User who performed the operation")
    operation: OperationType = Field(..., description="Type of AI operation")
    provider: str = Field(..., description="AI provider (claude, openai, gemini)")
    model: str = Field(..., description="Specific model used")
    input_tokens: int = Field(..., ge=0, description="Number of input/prompt tokens")
    output_tokens: int = Field(..., ge=0, description="Number of output/completion tokens")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    context: Optional[str] = Field(None, description="Topic name or filenames")
    course_id: Optional[str] = Field(None, description="Associated course ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "operation": "CHAPTER_GENERATION",
                "provider": "claude",
                "model": "claude-3-5-sonnet-20241022",
                "input_tokens": 1500,
                "output_tokens": 3000,
                "total_tokens": 4500,
                "context": "Introduction to Machine Learning",
                "course_id": "507f1f77bcf86cd799439012"
            }
        }


class TokenUsageInDB(TokenUsageRecord):
    """Token usage record as stored in database."""
    id: Optional[str] = Field(None, alias="_id")

    class Config:
        populate_by_name = True


class TokenUsageResponse(BaseModel):
    """Response containing paginated token usage records."""
    records: List[TokenUsageInDB]
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_records: int
    limit: int
    offset: int


class TokenUsageSummary(BaseModel):
    """Aggregated summary of token usage."""
    by_operation: Dict[str, int] = Field(
        default_factory=dict,
        description="Total tokens by operation type"
    )
    by_provider: Dict[str, int] = Field(
        default_factory=dict,
        description="Total tokens by AI provider"
    )
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    record_count: int = 0

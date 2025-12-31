"""
User models for authentication and enrollment.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    """Request model for user signup."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response model for user data (excludes password)."""
    id: str
    name: str
    email: str
    enrolled_courses: List[str] = []
    created_at: datetime


class UserInDB(BaseModel):
    """Internal user model with hashed password."""
    id: str
    name: str
    email: str
    hashed_password: str
    enrolled_courses: List[str] = []
    created_at: datetime


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserCourseEnrollment(BaseModel):
    """Tracks when user enrolled in a course."""
    user_id: str
    course_id: str
    enrolled_at: datetime
    progress: Dict[str, Any] = {}  # Future: track progress per course

"""
Courses API Router
Handles all course-related endpoints with configurable AI providers.
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from app.models.course import GenerateCourseRequest, GenerateCourseResponse, Chapter
from app.models.validation import TopicValidationResult
from app.services.ai_service_factory import AIServiceFactory
from app.services.topic_validator import get_topic_validator
from app.config import UseCase
from app.db import crud

# Create router
router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateCourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate course chapters from a topic",
    description="Takes a topic as input and generates a structured course with multiple chapters. Supports multiple AI providers."
)
async def generate_course(
    request: GenerateCourseRequest,
    provider: Optional[str] = Query(
        None, 
        description="AI provider to use: 'claude', 'openai', or 'mock'. If not specified, uses default from config."
    )
):
    """
    Generate a course with chapters based on the provided topic and difficulty.

    Args:
        request: Request body containing the topic and difficulty level
        provider: Optional AI provider override (claude/openai/mock)

    Returns:
        GenerateCourseResponse with generated chapters

    Raises:
        HTTPException: If topic is invalid or generation fails

    Examples:
        # Use default provider with beginner difficulty
        POST /api/v1/courses/generate
        {"topic": "Project Management", "difficulty": "beginner"}

        # Force use of mock provider with advanced difficulty
        POST /api/v1/courses/generate?provider=mock
        {"topic": "Project Management", "difficulty": "advanced"}

        # Use Claude with intermediate difficulty (default)
        POST /api/v1/courses/generate?provider=claude
        {"topic": "Project Management"}
    """
    try:
        # Validate topic is not empty
        if not request.topic or not request.topic.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic cannot be empty"
            )

        # Step 1: Validate topic using TopicValidator
        validator = get_topic_validator()
        validation_result = await validator.validate(request.topic)

        if validation_result.status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "topic_rejected",
                    "reason": validation_result.reason,
                    "message": validation_result.message,
                    "suggestions": validation_result.suggestions
                }
            )

        if validation_result.status == "needs_clarification":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "topic_needs_clarification",
                    "reason": validation_result.reason,
                    "message": validation_result.message,
                    "suggestions": validation_result.suggestions
                }
            )

        # Step 2: Check cache first
        cached_course = await crud.get_course_by_topic(request.topic, request.difficulty)
        if cached_course:
            # Return cached course
            chapters = [Chapter(**ch) for ch in cached_course["chapters"]]
            return GenerateCourseResponse(
                topic=cached_course["original_topic"],
                total_chapters=len(chapters),
                chapters=chapters,
                message=f"Retrieved {len(chapters)} {request.difficulty}-level chapters for '{request.topic}' from cache"
            )

        # Get the appropriate AI service
        ai_service = AIServiceFactory.get_service(
            use_case=UseCase.CHAPTER_GENERATION,
            provider_override=provider
        )

        # Generate chapters with user-specified difficulty
        chapters = await ai_service.generate_chapters(request.topic, request.difficulty)

        # Determine which provider was actually used
        actual_provider = ai_service.get_provider_name()

        # Save to cache (non-blocking, don't fail if DB is down)
        await crud.save_course(
            topic=request.topic,
            difficulty=request.difficulty,
            chapters=chapters,
            provider=actual_provider
        )

        # Create response
        response = GenerateCourseResponse(
            topic=request.topic,
            total_chapters=len(chapters),
            chapters=chapters,
            message=f"Generated {len(chapters)} {request.difficulty}-level chapters for '{request.topic}' using {actual_provider}"
        )

        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Handle configuration errors (e.g., missing API keys)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Catch any other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate course: {str(e)}"
        )


@router.post(
    "/validate-topic",
    response_model=TopicValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate a topic before course generation",
    description="Checks if a topic is suitable for course generation. Returns validation status, suggestions, and complexity assessment."
)
async def validate_topic(
    request: GenerateCourseRequest
):
    """
    Validate a topic before generating a course.

    This endpoint allows the frontend to check if a topic is valid
    before submitting for course generation. Useful for real-time
    validation and providing user feedback.

    Args:
        request: Request body containing the topic

    Returns:
        TopicValidationResult with status, suggestions, and complexity

    Examples:
        # Valid topic
        POST /api/v1/courses/validate-topic
        {"topic": "Python Web Development", "difficulty": "beginner"}
        -> {"status": "accepted", "complexity": {...}}

        # Too broad
        POST /api/v1/courses/validate-topic
        {"topic": "Physics", "difficulty": "beginner"}
        -> {"status": "rejected", "reason": "too_broad", "suggestions": [...]}
    """
    validator = get_topic_validator()
    return await validator.validate(request.topic)


@router.get(
    "/providers",
    response_model=dict,
    summary="Get AI provider configuration",
    description="Returns information about available AI providers and current configuration."
)
async def get_provider_info():
    """
    Get information about configured AI providers.
    
    Returns:
        Dictionary with provider configuration and availability
        
    Example Response:
        {
            "default_provider": "claude",
            "available_providers": ["mock", "claude"],
            "models": {
                "chapter_generation": "claude-sonnet-4-20250514",
                "question_generation": "claude-sonnet-4-20250514",
                ...
            }
        }
    """
    return AIServiceFactory.get_provider_info()


@router.get(
    "/supported-topics",
    response_model=dict,
    summary="Get list of topics with specific mock data",
    description="Returns topics that have predefined mock data (only relevant when using mock provider)."
)
async def get_supported_topics():
    """
    Get list of topics that have specific mock data.
    Only relevant when using the mock provider.
    
    Returns:
        Dictionary with list of supported topics
    """
    # Get mock service to check supported topics
    mock_service = AIServiceFactory.get_service(
        use_case=UseCase.CHAPTER_GENERATION,
        provider_override="mock"
    )
    
    topics = mock_service.get_supported_topics()
    
    return {
        "supported_topics": topics,
        "note": "These topics have specific mock data. Other topics will use generic templates. Only applies to mock provider."
    }
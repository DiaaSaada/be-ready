"""
Courses API Router
Handles all course-related endpoints with configurable AI providers.
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
from app.models.course import (
    GenerateCourseRequest,
    GenerateCourseResponse,
    Chapter,
    CourseConfig
)
from app.models.validation import TopicValidationResult
from app.models.responses import CourseSummary, MyCoursesResponse
from app.models.user import UserInDB
from app.dependencies.auth import get_current_user
from app.services.ai_service_factory import AIServiceFactory
from app.services.topic_validator import get_topic_validator
from app.services.course_configurator import get_course_configurator
from app.config import UseCase
from app.db import crud, user_repository

# Create router
router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateCourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate course chapters from a topic",
    description="Takes a topic and difficulty as input, validates the topic, configures optimal course structure, and generates chapters using AI."
)
async def generate_course(
    request: GenerateCourseRequest,
    provider: Optional[str] = Query(
        None,
        description="AI provider to use: 'claude', 'openai', or 'mock'. If not specified, uses default from config."
    ),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a course with chapters based on the provided topic and difficulty.

    Flow:
    1. Validate topic using TopicValidator (unless skip_validation=True)
    2. Get optimal course configuration from CourseConfigurator
    3. Check cache for existing course
    4. Generate chapters using AI with the configuration
    5. Save to cache and return enriched response

    Args:
        request: Request body containing topic, difficulty, and skip_validation flag
        provider: Optional AI provider override (claude/openai/mock)

    Returns:
        GenerateCourseResponse with chapters and study time estimates

    Raises:
        HTTPException 400: If topic is rejected (too broad, inappropriate, etc.)
        HTTPException 422: If topic needs clarification
        HTTPException 500: If generation fails
    """
    try:
        # Validate topic is not empty
        if not request.topic or not request.topic.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic cannot be empty"
            )

        complexity_score = None
        category = None

        # Step 1: Validate topic (unless skipped for testing)
        if not request.skip_validation:
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

            # Extract complexity score and category from validation
            if validation_result.complexity:
                complexity_score = validation_result.complexity.score
            if validation_result.category:
                category = validation_result.category.value

        # Step 2: Get optimal course configuration
        configurator = get_course_configurator()
        # Use complexity score from validation, default to 5 if not available
        config = configurator.get_config(
            complexity_score=complexity_score or 5,
            difficulty=request.difficulty
        )

        # Step 3: Get the appropriate AI service and generate chapters
        ai_service = AIServiceFactory.get_service(
            use_case=UseCase.CHAPTER_GENERATION,
            provider_override=provider
        )

        # Generate chapters with configuration
        chapters = await ai_service.generate_chapters(
            topic=request.topic,
            config=config
        )

        # Determine which provider was actually used
        actual_provider = ai_service.get_provider_name()

        # Step 4: Save course for the authenticated user
        course_id = await crud.save_course_for_user(
            user_id=current_user.id,
            topic=request.topic,
            difficulty=request.difficulty,
            complexity_score=complexity_score,
            category=category,
            chapters=chapters,
            provider=actual_provider
        )

        # Step 5: Auto-enroll user in the newly created course
        await user_repository.enroll_user_in_course(current_user.id, course_id)

        # Create enriched response with course ID
        response = GenerateCourseResponse(
            id=course_id,
            topic=request.topic,
            difficulty=request.difficulty,
            category=category,
            total_chapters=len(chapters),
            estimated_study_hours=config.estimated_study_hours,
            time_per_chapter_minutes=config.time_per_chapter_minutes,
            complexity_score=complexity_score,
            chapters=chapters,
            config=config,
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
    "/validate",
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
        POST /api/v1/courses/validate
        {"topic": "Python Web Development", "difficulty": "beginner"}
        -> {"status": "accepted", "complexity": {...}}

        POST /api/v1/courses/validate
        {"topic": "Physics", "difficulty": "beginner"}
        -> {"status": "rejected", "reason": "too_broad", "suggestions": [...]}
    """
    validator = get_topic_validator()
    return await validator.validate(request.topic)


@router.post(
    "/validate-topic",
    response_model=TopicValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate a topic (alias)",
    description="Alias for /validate endpoint.",
    include_in_schema=False  # Hide from docs, use /validate instead
)
async def validate_topic_alias(request: GenerateCourseRequest):
    """Alias for /validate endpoint for backwards compatibility."""
    return await validate_topic(request)


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
    """
    return AIServiceFactory.get_provider_info()


@router.get(
    "/config-presets",
    response_model=dict,
    summary="Get course configuration presets",
    description="Returns the difficulty presets used for course configuration."
)
async def get_config_presets():
    """
    Get course configuration presets for each difficulty level.

    Returns:
        Dictionary with presets for beginner, intermediate, and advanced
    """
    configurator = get_course_configurator()
    return {
        "presets": configurator.get_all_presets(),
        "description": {
            "beginner": "Shorter chapters with high-level overviews",
            "intermediate": "Balanced depth with practical examples",
            "advanced": "Comprehensive coverage with expert-level content"
        }
    }


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


# =============================================================================
# User's Created Courses Endpoints
# =============================================================================

@router.get(
    "/my-courses",
    response_model=MyCoursesResponse,
    summary="Get my created courses",
    description="Returns all courses created by the authenticated user."
)
async def get_my_created_courses(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all courses created by the current user.

    Returns:
        MyCoursesResponse with list of user's courses and total count
    """
    courses = await crud.get_courses_by_user(current_user.id)

    # Map to CourseSummary format
    course_summaries = []
    for course in courses:
        summary = CourseSummary(
            id=course.get("id", str(course.get("_id", ""))),
            topic=course.get("original_topic", course.get("topic", "")),
            difficulty=course.get("difficulty", "intermediate"),
            complexity_score=course.get("complexity_score"),
            total_chapters=course.get("total_chapters", len(course.get("chapters", []))),
            questions_generated=False,
            created_at=course.get("created_at")
        )
        course_summaries.append(summary)

    return MyCoursesResponse(
        courses=course_summaries,
        total_count=len(course_summaries)
    )


@router.get(
    "/{course_id}",
    response_model=GenerateCourseResponse,
    summary="Get a course by ID",
    description="Returns a single course by its ID if owned by the authenticated user."
)
async def get_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get a specific course by ID.

    Args:
        course_id: MongoDB ObjectId as string

    Returns:
        GenerateCourseResponse with course details

    Raises:
        HTTPException 404: If course not found or not owned by user
    """
    course = await crud.get_course_by_id(course_id)

    if not course or course.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Convert to response format
    chapters = [Chapter(**ch) for ch in course.get("chapters", [])]

    return GenerateCourseResponse(
        id=course.get("id"),
        topic=course.get("original_topic", course.get("topic", "")),
        difficulty=course.get("difficulty", "intermediate"),
        category=course.get("category"),
        total_chapters=len(chapters),
        estimated_study_hours=0,  # Not stored in DB
        time_per_chapter_minutes=0,  # Not stored in DB
        complexity_score=course.get("complexity_score"),
        chapters=chapters,
        message="Course retrieved successfully"
    )


@router.delete(
    "/{course_id}",
    summary="Delete a course",
    description="Deletes a course if owned by the authenticated user."
)
async def delete_course(
    course_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Delete a course by ID.

    Args:
        course_id: MongoDB ObjectId as string

    Returns:
        Success message

    Raises:
        HTTPException 404: If course not found or not owned by user
    """
    deleted = await crud.delete_course(course_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return {"message": "Course deleted successfully"}

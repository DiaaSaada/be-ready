"""
Courses API Router
Handles all course-related endpoints with configurable AI providers.
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File, Form
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import os
from app.models.course import (
    GenerateCourseRequest,
    GenerateCourseResponse,
    GenerateFromFilesResponse,
    FileUploadResult,
    Chapter,
    CourseConfig
)
from app.models.validation import TopicValidationResult
from app.models.responses import CourseSummary, MyCoursesResponse
from app.models.user import UserInDB
from app.models.document_analysis import (
    DocumentAnalysisResponse,
    DocumentOutline,
    ConfirmOutlineRequest,
    ConfirmedSection
)
from app.dependencies.auth import get_current_user
from app.services.ai_service_factory import AIServiceFactory
from app.services.topic_validator import get_topic_validator
from app.services.course_configurator import get_course_configurator
from app.services.file_parser import get_file_parser
from app.config import UseCase, settings
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
        print( "user_id", current_user.id)
        # Step 1: Validate topic (unless skipped for testing)
        if not request.skip_validation:
            validator = get_topic_validator()
            print( "user_id", current_user.id)
            validation_result = await validator.validate(request.topic, user_id=current_user.id)

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
        print( "user_id2", current_user.id)
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
            config=config,
            user_id=current_user.id,
            context=request.topic
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
    request: GenerateCourseRequest,
    current_user: UserInDB = Depends(get_current_user)
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
    print("validate user id ", current_user.id )
    validator = get_topic_validator()
    return await validator.validate(request.topic, current_user.id)


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


@router.post(
    "/generate-from-files",
    response_model=GenerateFromFilesResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate course from uploaded files",
    description="Upload PDF, DOCX, or TXT files to generate a course based on their content."
)
async def generate_course_from_files(
    files: List[UploadFile] = File(..., description="Files to process (PDF, DOCX, TXT)"),
    topic: Optional[str] = Form(default=None, description="Optional course title"),
    difficulty: str = Form(default="intermediate", description="Difficulty level"),
    provider: Optional[str] = Query(default=None, description="AI provider override"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a course with chapters based on uploaded file content.

    Flow:
    1. Validate file count and types
    2. Save files temporarily and parse content
    3. Infer topic from content if not provided
    4. Generate chapters using AI with content context
    5. Store course with source metadata
    6. Clean up temporary files
    """
    # Validate file count
    if len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_upload_files} files allowed"
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required"
        )

    # Validate file extensions
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' has unsupported type. Allowed: {settings.allowed_extensions}"
            )

    # Check file sizes and read content
    file_contents = []
    for file in files:
        content = await file.read()
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' exceeds maximum size of {settings.max_upload_size // (1024*1024)}MB"
            )
        file_contents.append((file.filename, content))
        await file.seek(0)

    # Save files temporarily and parse
    temp_dir = Path(settings.upload_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []
    file_paths = []

    try:
        # Save uploaded files temporarily
        for filename, content in file_contents:
            temp_path = temp_dir / f"{uuid.uuid4()}_{filename}"
            with open(temp_path, 'wb') as f:
                f.write(content)
            temp_files.append(temp_path)
            file_paths.append(temp_path)

        # Parse all files
        parser = get_file_parser()
        parse_result = await parser.parse_files(file_paths)

        # Check if we have enough content
        if parse_result.total_chars < settings.min_content_chars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extracted content is too short ({parse_result.total_chars} chars). "
                       f"Minimum {settings.min_content_chars} chars required."
            )

        # If all files failed, return error
        if parse_result.successful_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "all_files_failed",
                    "message": "Could not extract content from any uploaded file",
                    "errors": parse_result.errors
                }
            )

        # Infer topic from content if not provided
        inferred_topic = topic.strip() if topic and topic.strip() else None
        if not inferred_topic:
            # Use first 100 chars of content as topic, or first line
            first_content = parse_result.combined_content[:500]
            lines = first_content.split('\n')
            # Find first non-empty, non-header line
            for line in lines:
                clean_line = line.strip().strip('=').strip()
                if clean_line and not clean_line.startswith('Content from:'):
                    inferred_topic = clean_line[:100]
                    break
            if not inferred_topic:
                inferred_topic = "Study Guide from Uploaded Files"

        # Get course configuration (use default complexity 5 for file-based)
        configurator = get_course_configurator()
        config = configurator.get_config(
            complexity_score=5,
            difficulty=difficulty
        )

        # Adjust chapters for small content
        if parse_result.total_chars < 2000:
            config.recommended_chapters = max(1, config.recommended_chapters // 2)

        # Generate chapters with content
        ai_service = AIServiceFactory.get_service(
            use_case=UseCase.CHAPTER_GENERATION,
            provider_override=provider
        )

        # Build context from filenames
        file_context = ", ".join([f.filename for f in parse_result.files if f.success])

        chapters = await ai_service.generate_chapters(
            topic=inferred_topic,
            config=config,
            content=parse_result.combined_content,
            user_id=current_user.id,
            context=file_context or inferred_topic
        )

        actual_provider = ai_service.get_provider_name()

        # Prepare source file metadata
        source_files_meta = [
            {
                "filename": f.filename,
                "file_type": f.file_type,
                "char_count": f.char_count,
                "success": f.success,
                "error": f.error
            }
            for f in parse_result.files
        ]

        # Save course
        course_id = await crud.save_course_from_files(
            user_id=current_user.id,
            topic=inferred_topic,
            difficulty=difficulty,
            complexity_score=5,
            category=None,
            chapters=chapters,
            provider=actual_provider,
            source_files=source_files_meta
        )

        # Auto-enroll user
        if course_id:
            await user_repository.enroll_user_in_course(current_user.id, course_id)

        # Build response
        file_results = [
            FileUploadResult(
                filename=f.filename,
                file_type=f.file_type,
                char_count=f.char_count,
                success=f.success,
                error=f.error
            )
            for f in parse_result.files
        ]

        return GenerateFromFilesResponse(
            id=course_id,
            topic=inferred_topic,
            difficulty=difficulty,
            total_chapters=len(chapters),
            estimated_study_hours=config.estimated_study_hours,
            time_per_chapter_minutes=config.time_per_chapter_minutes,
            complexity_score=5,
            chapters=chapters,
            message=f"Generated {len(chapters)} chapters from {parse_result.successful_count} file(s)",
            source_files=file_results,
            extracted_text_chars=parse_result.total_chars,
            config=config
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate course from files: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except Exception:
                pass


@router.post(
    "/analyze-files",
    response_model=DocumentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze uploaded files for document structure",
    description="Phase 1: Upload files and get detected chapter structure for user review."
)
async def analyze_files_for_structure(
    files: List[UploadFile] = File(..., description="Files to analyze (PDF, DOCX, TXT)"),
    provider: Optional[str] = Query(default=None, description="AI provider override"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Analyze uploaded files and return detected document structure.

    This is Phase 1 of the two-phase file-to-course flow.
    The detected structure is shown to the user for review before
    generating detailed chapters.

    Flow:
    1. Validate and parse uploaded files
    2. Use AI to detect natural sections/chapters
    3. Store analysis temporarily (30 min TTL)
    4. Return structure for user review
    """
    # Validate file count
    if len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_upload_files} files allowed"
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required"
        )

    # Validate file extensions
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' has unsupported type. Allowed: {settings.allowed_extensions}"
            )

    # Check file sizes and read content
    file_contents = []
    for file in files:
        content = await file.read()
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' exceeds maximum size of {settings.max_upload_size // (1024*1024)}MB"
            )
        file_contents.append((file.filename, content))
        await file.seek(0)

    # Save files temporarily and parse
    temp_dir = Path(settings.upload_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []
    file_paths = []

    try:
        # Save uploaded files temporarily
        for filename, content in file_contents:
            temp_path = temp_dir / f"{uuid.uuid4()}_{filename}"
            with open(temp_path, 'wb') as f:
                f.write(content)
            temp_files.append(temp_path)
            file_paths.append(temp_path)

        # Parse all files
        parser = get_file_parser()
        parse_result = await parser.parse_files(file_paths)

        # Check if we have enough content
        if parse_result.total_chars < settings.min_content_chars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extracted content is too short ({parse_result.total_chars} chars). "
                       f"Minimum {settings.min_content_chars} chars required."
            )

        # If all files failed, return error
        if parse_result.successful_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "all_files_failed",
                    "message": "Could not extract content from any uploaded file",
                    "errors": parse_result.errors
                }
            )

        # Use AI to analyze document structure - analyze each file separately
        ai_service = AIServiceFactory.get_service(
            use_case=UseCase.DOCUMENT_ANALYSIS,
            provider_override=provider
        )

        # Analyze each file separately to preserve source attribution
        all_sections = []
        document_titles = []
        document_types = []
        total_time = 0

        successful_files = [f for f in parse_result.files if f.success and f.content.strip()]

        # Build context from all filenames
        all_filenames = ", ".join([f.filename for f in successful_files])

        print(f"[ROUTER] About to analyze {len(successful_files)} files for user {current_user.id}")

        for parsed_file in successful_files:
            print(f"[ROUTER] Calling analyze_document_structure for {parsed_file.filename}")
            file_outline = await ai_service.analyze_document_structure(
                content=parsed_file.content,
                max_sections=15,
                user_id=current_user.id,
                context=parsed_file.filename
            )
            print(f"[ROUTER] Finished analyzing {parsed_file.filename}")

            # Add source_file to each section and collect them
            for section in file_outline.sections:
                section.source_file = parsed_file.filename
                all_sections.append(section)

            document_titles.append(file_outline.document_title)
            document_types.append(file_outline.document_type)
            total_time += file_outline.estimated_total_time_minutes

        # Renumber sections sequentially
        for i, section in enumerate(all_sections):
            section.order = i + 1

        # Build combined outline
        combined_title = document_titles[0] if len(document_titles) == 1 else " + ".join(document_titles[:3])
        if len(document_titles) > 3:
            combined_title += f" (+{len(document_titles) - 3} more)"

        # Determine most common document type
        document_type = max(set(document_types), key=document_types.count) if document_types else "notes"

        document_outline = DocumentOutline(
            document_title=combined_title,
            document_type=document_type,
            total_sections=len(all_sections),
            sections=all_sections,
            estimated_total_time_minutes=total_time,
            analysis_notes=f"Analyzed {len(successful_files)} file(s) with {len(all_sections)} total sections."
        )

        # Prepare source file metadata
        source_files_meta = [
            {
                "filename": f.filename,
                "file_type": f.file_type,
                "char_count": f.char_count,
                "success": f.success,
                "error": f.error
            }
            for f in parse_result.files
        ]

        # Store analysis temporarily with TTL
        analysis_id = await crud.save_document_analysis(
            user_id=current_user.id,
            outline=document_outline.model_dump(),
            raw_content=parse_result.combined_content,
            source_files=source_files_meta,
            expires_in_minutes=settings.analysis_expiry_minutes
        )

        if not analysis_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store document analysis"
            )

        # Build response
        file_results = [
            FileUploadResult(
                filename=f.filename,
                file_type=f.file_type,
                char_count=f.char_count,
                success=f.success,
                error=f.error
            )
            for f in parse_result.files
        ]

        expires_at = datetime.utcnow() + timedelta(minutes=settings.analysis_expiry_minutes)

        return DocumentAnalysisResponse(
            analysis_id=analysis_id,
            document_outline=document_outline,
            source_files=file_results,
            extracted_text_chars=parse_result.total_chars,
            expires_at=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze files: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except Exception:
                pass


@router.post(
    "/generate-from-outline",
    response_model=GenerateFromFilesResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate course from confirmed document outline",
    description="Phase 2: Generate detailed chapters from user-confirmed structure."
)
async def generate_from_confirmed_outline(
    request: ConfirmOutlineRequest,
    provider: Optional[str] = Query(default=None, description="AI provider override"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate chapters based on user-confirmed document structure.

    This is Phase 2 of the two-phase file-to-course flow.

    Flow:
    1. Retrieve stored analysis by analysis_id
    2. Filter to included sections only
    3. Generate detailed chapters with key_ideas
    4. Save course with source metadata
    5. Clean up analysis document
    """
    # Retrieve stored analysis
    analysis = await crud.get_document_analysis(request.analysis_id, current_user.id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or expired. Please upload files again."
        )

    # Get confirmed sections that are included
    included_sections = [s for s in request.confirmed_sections if s.include]

    if not included_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one section must be included"
        )

    try:
        # Get topic from request or stored outline
        topic = request.custom_topic
        if not topic or not topic.strip():
            topic = analysis["outline"].get("document_title", "Study Guide")

        # Generate chapters from outline
        ai_service = AIServiceFactory.get_service(
            use_case=UseCase.CHAPTER_GENERATION,
            provider_override=provider
        )

        # Build context from source files
        source_files = analysis.get("source_files", [])
        file_context = ", ".join([f.get("filename", "") for f in source_files if f.get("success")])

        chapters = await ai_service.generate_chapters_from_outline(
            topic=topic,
            content=analysis["raw_content"],
            confirmed_sections=request.confirmed_sections,
            difficulty=request.difficulty,
            user_id=current_user.id,
            context=file_context or topic
        )

        actual_provider = ai_service.get_provider_name()

        # Get course configuration for response
        configurator = get_course_configurator()
        config = configurator.get_config(
            complexity_score=5,
            difficulty=request.difficulty
        )

        # Prepare source file metadata from stored analysis
        source_files_meta = analysis.get("source_files", [])

        # Save course
        course_id = await crud.save_course_from_files(
            user_id=current_user.id,
            topic=topic,
            difficulty=request.difficulty,
            complexity_score=5,
            category=None,
            chapters=chapters,
            provider=actual_provider,
            source_files=source_files_meta
        )

        # Auto-enroll user
        if course_id:
            await user_repository.enroll_user_in_course(current_user.id, course_id)

        # Clean up stored analysis
        await crud.delete_document_analysis(request.analysis_id)

        # Build response
        file_results = [
            FileUploadResult(
                filename=f.get("filename", ""),
                file_type=f.get("file_type", ""),
                char_count=f.get("char_count", 0),
                success=f.get("success", True),
                error=f.get("error")
            )
            for f in source_files_meta
        ]

        return GenerateFromFilesResponse(
            id=course_id,
            topic=topic,
            difficulty=request.difficulty,
            total_chapters=len(chapters),
            estimated_study_hours=config.estimated_study_hours,
            time_per_chapter_minutes=config.time_per_chapter_minutes,
            complexity_score=5,
            chapters=chapters,
            message=f"Generated {len(chapters)} chapters from confirmed outline",
            source_files=file_results,
            extracted_text_chars=len(analysis.get("raw_content", "")),
            config=config
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate course from outline: {str(e)}"
        )


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

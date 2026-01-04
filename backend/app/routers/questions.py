"""
Questions API Router
Handles question generation and analysis endpoints.
"""
import time
from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from app.models.course import Chapter
from app.models.question import (
    QuestionGenerationConfig,
    ChapterQuestions,
    GenerateQuestionsResponse,
)
from app.services.question_analyzer import get_question_analyzer, QuestionCountRecommendation
from app.services.question_generator import get_question_generator
from app.services.ai_service_factory import AIServiceFactory
from app.config import settings, UseCase
from app.db import crud
from app.models.user import UserInDB
from app.dependencies.auth import get_current_user


# Create router
router = APIRouter()


# Request/Response models specific to this router
class GenerateQuestionsRequest(BaseModel):
    """Request model for generating questions."""
    topic: str = Field(..., min_length=1, max_length=200, description="Course topic")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Course difficulty level"
    )
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_title: str = Field(..., min_length=1, max_length=200, description="Chapter title")
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Key concepts to cover in questions"
    )
    override_mcq_count: Optional[int] = Field(
        default=None, ge=5, le=40,
        description="Override recommended MCQ count"
    )
    override_tf_count: Optional[int] = Field(
        default=None, ge=3, le=15,
        description="Override recommended True/False count"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AWS Solutions Architect",
                "difficulty": "advanced",
                "chapter_number": 1,
                "chapter_title": "Introduction to AWS",
                "key_concepts": ["EC2", "S3", "VPC", "IAM"],
                "override_mcq_count": None,
                "override_tf_count": None
            }
        }


class AnalyzeCountRequest(BaseModel):
    """Request model for analyzing question count."""
    topic: str = Field(..., min_length=1, max_length=200, description="Course topic")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Course difficulty level"
    )
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_title: str = Field(..., min_length=1, max_length=200, description="Chapter title")
    chapter_summary: str = Field(
        default="", max_length=1000,
        description="Brief summary of the chapter"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Key concepts in the chapter"
    )
    estimated_time_minutes: int = Field(
        default=30, ge=5, le=180,
        description="Estimated time for the chapter in minutes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AWS Solutions Architect",
                "difficulty": "advanced",
                "chapter_number": 1,
                "chapter_title": "EC2 and Compute",
                "chapter_summary": "Learn about EC2 instances, auto scaling, and load balancing.",
                "key_concepts": ["EC2", "Auto Scaling", "Load Balancers", "EBS"],
                "estimated_time_minutes": 90
            }
        }


class GenerateQuestionsFullResponse(BaseModel):
    """Full response model for question generation."""
    chapter_number: int = Field(..., description="Chapter number")
    chapter_title: str = Field(..., description="Chapter title")
    total_questions: int = Field(..., description="Total number of questions")
    total_points: int = Field(..., description="Total points available")
    mcq_questions: list = Field(..., description="List of MCQ questions")
    true_false_questions: list = Field(..., description="List of True/False questions")
    generation_info: dict = Field(..., description="Generation metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_number": 1,
                "chapter_title": "Introduction to AWS",
                "total_questions": 13,
                "total_points": 13,
                "mcq_questions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "type": "mcq",
                        "difficulty": "medium",
                        "question_text": "What is Amazon EC2?",
                        "options": [
                            "A) A scalable compute service in the cloud",
                            "B) A database service",
                            "C) A content delivery network",
                            "D) A messaging queue service"
                        ],
                        "correct_answer": "A",
                        "explanation": "EC2 (Elastic Compute Cloud) provides scalable computing capacity in the AWS cloud.",
                        "points": 1
                    }
                ],
                "true_false_questions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "type": "true_false",
                        "difficulty": "easy",
                        "question_text": "AWS EC2 instances can be resized after launch.",
                        "correct_answer": True,
                        "explanation": "True. EC2 instances can be stopped and resized to a different instance type.",
                        "points": 1
                    }
                ],
                "generation_info": {
                    "model": "claude-3-5-haiku-20241022",
                    "audience": "professionals or experts seeking deep understanding",
                    "provider": "claude",
                    "recommended_mcq": 8,
                    "recommended_tf": 5,
                    "actual_mcq": 8,
                    "actual_tf": 5,
                    "generation_time_ms": 2500
                }
            }
        }


@router.post(
    "/generate",
    response_model=GenerateQuestionsFullResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate questions for a chapter",
    description="Generates MCQ and True/False questions for a chapter using AI. Automatically determines optimal question count based on topic complexity."
)
async def generate_questions(
    request: GenerateQuestionsRequest,
    provider: Optional[str] = Query(
        None,
        description="AI provider to use: 'claude', 'openai', or 'mock'. If not specified, uses default from config."
    ),
    chunked: bool = Query(
        False,
        description="Generate questions per key_concept in separate API calls. More reliable for large question sets but slower."
    ),
    skip_cache: bool = Query(
        False,
        description="Skip cache and force regeneration of questions."
    ),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate questions for a chapter.

    Flow:
    1. Validate request
    2. Use QuestionAnalyzer to get recommended counts (or use override)
    3. Build QuestionGenerationConfig
    4. Call QuestionGenerator.generate_questions()
    5. Return ChapterQuestions with generation info

    Args:
        request: Request body with topic, difficulty, chapter info, and optional overrides
        provider: Optional AI provider override (claude/openai/mock)

    Returns:
        Generated questions with metadata

    Raises:
        HTTPException 400: If request is invalid
        HTTPException 500: If generation fails
    """
    try:
        start_time = time.time()

        # Step 0: Check cache first (unless skip_cache is True)
        if not skip_cache:
            cached = await crud.get_questions(
                course_topic=request.topic,
                difficulty=request.difficulty,
                chapter_number=request.chapter_number
            )
            if cached:
                generation_time = int((time.time() - start_time) * 1000)
                return GenerateQuestionsFullResponse(
                    chapter_number=cached["chapter_number"],
                    chapter_title=cached["chapter_title"],
                    total_questions=len(cached.get("mcq", [])) + len(cached.get("true_false", [])),
                    total_points=len(cached.get("mcq", [])) + len(cached.get("true_false", [])),
                    mcq_questions=cached.get("mcq", []),
                    true_false_questions=cached.get("true_false", []),
                    generation_info={
                        "model": settings.model_question_generation,
                        "audience": QuestionGenerationConfig.derive_audience(request.difficulty),
                        "provider": cached.get("provider", "cached"),
                        "cached": True,
                        "chunked_mode": False,
                        "recommended_mcq": len(cached.get("mcq", [])),
                        "recommended_tf": len(cached.get("true_false", [])),
                        "actual_mcq": len(cached.get("mcq", [])),
                        "actual_tf": len(cached.get("true_false", [])),
                        "generation_time_ms": generation_time,
                        "analyzer_reasoning": "Returned from cache"
                    }
                )

        # Step 1: Validate key concepts
        if not request.key_concepts:
            request.key_concepts = [f"{request.topic} fundamentals"]

        # Step 2: Get recommended question counts
        analyzer = get_question_analyzer()

        # Create a Chapter object for the analyzer
        chapter = Chapter(
            number=request.chapter_number,
            title=request.chapter_title,
            summary=f"Chapter on {request.topic}",
            key_concepts=request.key_concepts,
            difficulty=request.difficulty
        )

        recommendation = await analyzer.analyze_chapter(
            chapter=chapter,
            topic=request.topic,
            difficulty=request.difficulty
        )

        # Use overrides if provided
        mcq_count = request.override_mcq_count or recommendation.mcq_count
        tf_count = request.override_tf_count or recommendation.true_false_count

        # Step 3: Derive audience from difficulty
        audience = QuestionGenerationConfig.derive_audience(request.difficulty)

        # Step 4: Build config
        config = QuestionGenerationConfig(
            topic=request.topic,
            difficulty=request.difficulty,
            audience=audience,
            chapter_number=request.chapter_number,
            chapter_title=request.chapter_title,
            key_concepts=request.key_concepts,
            recommended_mcq_count=mcq_count,
            recommended_tf_count=tf_count
        )

        # Build context for token logging
        question_context = f"{request.topic} - Ch{request.chapter_number}: {request.chapter_title}"

        # Step 5: Get AI service and generate questions
        if provider == "mock":
            # Use mock service directly
            ai_service = AIServiceFactory.get_service(
                use_case=UseCase.QUESTION_GENERATION,
                provider_override="mock"
            )
            chapter_questions = await ai_service.generate_questions_from_config(
                config,
                user_id=current_user.id,
                context=question_context
            )
            actual_provider = "mock"
        else:
            # Use the question generator service
            generator = get_question_generator()
            if chunked:
                # Use chunked generation for reliability with large question sets
                chapter_questions = await generator.generate_questions_chunked(
                    config,
                    user_id=current_user.id,
                    context=question_context
                )
            else:
                # Use single-request generation (faster but may fail for large sets)
                chapter_questions = await generator.generate_questions(
                    config,
                    user_id=current_user.id,
                    context=question_context
                )
            actual_provider = provider or settings.default_ai_provider

        generation_time = int((time.time() - start_time) * 1000)

        # Step 6: Save to cache
        await crud.save_questions(
            course_topic=request.topic,
            difficulty=request.difficulty,
            chapter_number=request.chapter_number,
            chapter_title=request.chapter_title,
            mcq=[q.model_dump() for q in chapter_questions.mcq_questions],
            true_false=[q.model_dump() for q in chapter_questions.true_false_questions],
            provider=actual_provider
        )

        # Build response
        return GenerateQuestionsFullResponse(
            chapter_number=chapter_questions.chapter_number,
            chapter_title=chapter_questions.chapter_title,
            total_questions=chapter_questions.total_questions,
            total_points=chapter_questions.total_points,
            mcq_questions=[q.model_dump() for q in chapter_questions.mcq_questions],
            true_false_questions=[q.model_dump() for q in chapter_questions.true_false_questions],
            generation_info={
                "model": settings.model_question_generation,
                "audience": audience,
                "provider": actual_provider,
                "cached": False,
                "chunked_mode": chunked,
                "recommended_mcq": recommendation.mcq_count,
                "recommended_tf": recommendation.true_false_count,
                "actual_mcq": len(chapter_questions.mcq_questions),
                "actual_tf": len(chapter_questions.true_false_questions),
                "generation_time_ms": generation_time,
                "analyzer_reasoning": recommendation.reasoning
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post(
    "/analyze-count",
    response_model=QuestionCountRecommendation,
    status_code=status.HTTP_200_OK,
    summary="Analyze recommended question count",
    description="Returns recommended question count without generating questions. Useful for preview before generation."
)
async def analyze_question_count(
    request: AnalyzeCountRequest
):
    """
    Analyze and return recommended question count for a chapter.

    Uses AI to analyze topic complexity and chapter content to recommend
    the optimal number of MCQ and True/False questions.

    Args:
        request: Request body with chapter details

    Returns:
        QuestionCountRecommendation with mcq_count, tf_count, and reasoning

    Raises:
        HTTPException 500: If analysis fails
    """
    try:
        analyzer = get_question_analyzer()

        # Create a Chapter object for the analyzer
        chapter = Chapter(
            number=request.chapter_number,
            title=request.chapter_title,
            summary=request.chapter_summary or f"Chapter on {request.topic}",
            key_concepts=request.key_concepts or [f"{request.topic} concepts"],
            difficulty=request.difficulty,
            estimated_time_minutes=request.estimated_time_minutes
        )

        recommendation = await analyzer.analyze_chapter(
            chapter=chapter,
            topic=request.topic,
            difficulty=request.difficulty
        )

        return recommendation

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze question count: {str(e)}"
        )


@router.get(
    "/sample",
    response_model=GenerateQuestionsFullResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sample questions",
    description="Returns sample questions for testing UI. Uses mock service."
)
async def get_sample_questions(
    topic: str = Query(
        default="Python Programming",
        description="Sample topic"
    ),
    difficulty: Literal["beginner", "intermediate", "advanced"] = Query(
        default="intermediate",
        description="Difficulty level"
    ),
    mcq_count: int = Query(
        default=5, ge=1, le=20,
        description="Number of MCQ questions"
    ),
    tf_count: int = Query(
        default=3, ge=1, le=10,
        description="Number of True/False questions"
    )
):
    """
    Get sample questions for testing.

    Always uses the mock service to generate sample questions quickly
    without making actual AI API calls.

    Args:
        topic: Sample topic
        difficulty: Difficulty level
        mcq_count: Number of MCQ questions
        tf_count: Number of True/False questions

    Returns:
        Sample questions for the specified parameters
    """
    # Get mock service
    mock_service = AIServiceFactory.get_service(
        use_case=UseCase.QUESTION_GENERATION,
        provider_override="mock"
    )

    # Build config
    config = QuestionGenerationConfig(
        topic=topic,
        difficulty=difficulty,
        audience=QuestionGenerationConfig.derive_audience(difficulty),
        chapter_number=1,
        chapter_title=f"Sample {topic} Chapter",
        key_concepts=["Sample Concept 1", "Sample Concept 2", "Sample Concept 3"],
        recommended_mcq_count=mcq_count,
        recommended_tf_count=tf_count
    )

    # Generate sample questions
    chapter_questions = await mock_service.generate_questions_from_config(config)

    return GenerateQuestionsFullResponse(
        chapter_number=chapter_questions.chapter_number,
        chapter_title=chapter_questions.chapter_title,
        total_questions=chapter_questions.total_questions,
        total_points=chapter_questions.total_points,
        mcq_questions=[q.model_dump() for q in chapter_questions.mcq_questions],
        true_false_questions=[q.model_dump() for q in chapter_questions.true_false_questions],
        generation_info={
            "model": "mock",
            "audience": config.audience,
            "provider": "mock",
            "note": "Sample questions generated using mock service"
        }
    )


@router.get(
    "/config",
    response_model=dict,
    summary="Get question generation configuration",
    description="Returns current configuration for question generation."
)
async def get_question_config():
    """
    Get current question generation configuration.

    Returns:
        Dictionary with model, defaults, and audience mappings
    """
    return {
        "model": settings.model_question_generation,
        "model_analysis": settings.model_question_count_analysis,
        "max_tokens": settings.max_tokens_question,
        "default_counts": {
            "beginner": {"mcq": 8, "tf": 5},
            "intermediate": {"mcq": 12, "tf": 6},
            "advanced": {"mcq": 20, "tf": 8}
        },
        "audience_mapping": {
            "beginner": "teenagers and beginners; simple language",
            "intermediate": "college students and professionals; technical terms allowed",
            "advanced": "experienced professionals; industry jargon acceptable"
        },
        "limits": {
            "mcq": {"min": 5, "max": 40},
            "true_false": {"min": 3, "max": 15}
        }
    }

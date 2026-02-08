"""
Mentor API Router
Handles AI mentor feedback and gap quiz generation for weak areas.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import uuid
from datetime import datetime

from app.models.mentor import (
    MentorStatusResponse,
    MentorAnalysis,
    GenerateGapQuizRequest,
    MentorFeedbackResponse,
    GapQuiz,
    GapQuizQuestion,
)
from app.models.user import UserInDB
from app.dependencies.auth import get_current_user
from app.services.weak_area_analyzer import get_weak_area_analyzer
from app.services.ai_service_factory import AIServiceFactory
from app.config import settings, UseCase
from app.db import crud


router = APIRouter()


@router.get(
    "/status",
    response_model=MentorStatusResponse,
    summary="Check mentor availability",
    description="Check if the AI mentor is available for a course based on chapters completed."
)
async def get_mentor_status(
    course_slug: str = Query(..., description="Course slug identifier"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Check if mentor feature is available for the user on this course.

    The mentor becomes available after completing a minimum number of chapters
    (configurable via MENTOR_CHAPTERS_THRESHOLD, default: 3).

    Returns:
        MentorStatusResponse with availability info and stats
    """
    analyzer = get_weak_area_analyzer()
    status_response = await analyzer.get_mentor_status(
        user_id=str(current_user.id),
        course_slug=course_slug
    )
    return status_response


@router.get(
    "/analysis",
    response_model=MentorAnalysis,
    summary="Get weak area analysis",
    description="Get detailed analysis of user's weak areas on a course."
)
async def get_mentor_analysis(
    course_slug: str = Query(..., description="Course slug identifier"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get detailed weak area analysis for the user on this course.

    Identifies chapters where the user scored below the threshold
    (configurable via MENTOR_WEAK_SCORE_THRESHOLD, default: 0.7 / 70%).

    Returns:
        MentorAnalysis with weak areas and stats
    """
    analyzer = get_weak_area_analyzer()
    analysis = await analyzer.analyze_user_progress(
        user_id=str(current_user.id),
        course_slug=course_slug
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return analysis


@router.post(
    "/generate-quiz",
    response_model=MentorFeedbackResponse,
    summary="Generate gap covering quiz",
    description="Generate a quiz targeting weak areas with optional AI-generated extra questions."
)
async def generate_gap_quiz(
    request: GenerateGapQuizRequest,
    provider: Optional[str] = Query(None, description="Override AI provider (mock, claude, openai, gemini)"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generate a gap covering quiz for the user's weak areas.

    The quiz includes:
    1. Wrong answers from completed quizzes (always included, FREE)
    2. AI-generated extra questions targeting weak concepts (optional, costs tokens)

    Args:
        request: GenerateGapQuizRequest with course_slug and options
        provider: Optional AI provider override

    Returns:
        MentorFeedbackResponse with analysis, feedback text, and quiz
    """
    user_id = str(current_user.id)
    analyzer = get_weak_area_analyzer()

    # Get weak area analysis
    analysis = await analyzer.analyze_user_progress(
        user_id=user_id,
        course_slug=request.course_slug
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    if not analysis.mentor_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mentor not available. Complete at least {settings.mentor_chapters_threshold} chapters first."
        )

    # Get wrong answers (FREE - always included)
    wrong_answers = await analyzer.get_wrong_answers(
        user_id=user_id,
        course_slug=request.course_slug,
        include_hints=request.include_hints
    )

    # Get AI service for feedback and optional extra questions
    ai_service = AIServiceFactory.get_service(UseCase.GAP_QUIZ_GENERATION, provider_override=provider)

    # Generate mentor feedback text
    weak_areas_list = [area.chapter_title for area in analysis.weak_areas]
    feedback_text = await ai_service.generate_feedback(
        user_progress={
            "overall_score": analysis.average_score,
            "chapters_completed": analysis.total_chapters_completed,
            "total_chapters": analysis.total_chapters
        },
        weak_areas=weak_areas_list,
        user_id=user_id,
        context=request.course_slug
    )

    # Generate extra AI questions (optional, with caching)
    extra_questions = []
    cache_hit = False
    if request.generate_extra and analysis.weak_areas:
        # Compute hash for cache lookup
        weak_areas_hash = crud.compute_weak_areas_hash(
            [{"chapter_number": wa.chapter_number, "score": wa.score} for wa in analysis.weak_areas]
        )

        # Try cache first
        cached = await crud.get_cached_gap_quiz(
            user_id=user_id,
            course_slug=request.course_slug,
            weak_areas_hash=weak_areas_hash,
            include_hints=request.include_hints
        )

        if cached:
            # Cache hit - convert dicts back to GapQuizQuestion objects
            extra_questions = [GapQuizQuestion(**q) for q in cached]
            cache_hit = True
        else:
            # Cache miss - generate new questions
            extra_questions = await ai_service.generate_gap_quiz_questions(
                weak_areas=analysis.weak_areas,
                course_topic=analysis.course_topic,
                difficulty=analysis.difficulty,
                num_questions=request.extra_questions_count,
                include_hints=request.include_hints,
                user_id=user_id,
                context=request.course_slug
            )

            # Save to cache
            await crud.save_gap_quiz_cache(
                user_id=user_id,
                course_slug=request.course_slug,
                weak_areas_hash=weak_areas_hash,
                extra_questions=extra_questions,
                include_hints=request.include_hints,
                provider=provider or settings.default_ai_provider
            )

            # Add extra questions to chapter question pools for future regular quizzes
            await crud.add_gap_quiz_questions_to_chapters(
                course_topic=analysis.course_topic,
                difficulty=analysis.difficulty,
                extra_questions=extra_questions
            )

    # Build gap quiz
    gap_quiz = GapQuiz(
        id=str(uuid.uuid4()),
        course_slug=request.course_slug,
        user_id=user_id,
        wrong_answers=wrong_answers,
        extra_questions=extra_questions,
        total_questions=len(wrong_answers) + len(extra_questions),
        wrong_answers_count=len(wrong_answers),
        extra_questions_count=len(extra_questions),
        include_hints=request.include_hints,
        cache_hit=cache_hit,
        created_at=datetime.utcnow()
    )

    return MentorFeedbackResponse(
        analysis=analysis,
        feedback_text=feedback_text,
        quiz=gap_quiz
    )


@router.get(
    "/config",
    summary="Get mentor configuration",
    description="Get current mentor feature configuration settings."
)
async def get_mentor_config():
    """
    Get the current mentor configuration settings.

    Returns:
        Dictionary with current mentor settings
    """
    return {
        "chapters_threshold": settings.mentor_chapters_threshold,
        "weak_score_threshold": settings.mentor_weak_score_threshold,
        "model_gap_quiz": settings.model_gap_quiz,
        "max_tokens_gap_quiz": settings.max_tokens_gap_quiz
    }

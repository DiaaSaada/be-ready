"""
Progress API Router
Handles user progress tracking for quiz results.
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime
from app.models.progress import (
    SubmitQuizRequest,
    ProgressResponse,
    ProgressListResponse,
    ProgressSummary,
)
from app.db.connection import MongoDB

# Collection name
PROGRESS_COLLECTION = "user_progress"

# Create router
router = APIRouter()


@router.post(
    "/submit",
    response_model=ProgressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit quiz results",
    description="Save quiz results including all answers and calculated score."
)
async def submit_quiz_results(request: SubmitQuizRequest):
    """
    Submit quiz results to save progress.

    Creates or updates a progress record for the user's quiz attempt.
    If a record already exists for this user/topic/chapter, it will be replaced.
    """
    try:
        db = MongoDB.get_db()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )

        normalized_topic = request.topic.lower().strip()
        now = datetime.utcnow()

        # Calculate score
        score = request.correct_count / request.total_questions if request.total_questions > 0 else 0.0
        score_percent = int(score * 100)

        # Prepare answers for storage
        answers_data = [answer.model_dump() for answer in request.answers]

        # Document to save
        document = {
            "user_id": request.user_id,
            "course_topic": normalized_topic,
            "difficulty": request.difficulty,
            "chapter_number": request.chapter_number,
            "chapter_title": request.chapter_title,
            "answers": answers_data,
            "score": score,
            "total_questions": request.total_questions,
            "correct_answers": request.correct_count,
            "completed": True,
            "started_at": now,
            "completed_at": now,
            "updated_at": now
        }

        # Upsert - replace if exists, insert if not
        result = await db[PROGRESS_COLLECTION].replace_one(
            {
                "user_id": request.user_id,
                "course_topic": normalized_topic,
                "difficulty": request.difficulty,
                "chapter_number": request.chapter_number
            },
            document,
            upsert=True
        )

        return ProgressResponse(
            user_id=request.user_id,
            course_topic=normalized_topic,
            difficulty=request.difficulty,
            chapter_number=request.chapter_number,
            chapter_title=request.chapter_title,
            score=score,
            score_percent=score_percent,
            correct_answers=request.correct_count,
            total_questions=request.total_questions,
            completed=True,
            completed_at=now,
            created_at=now
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save progress: {str(e)}"
        )


@router.get(
    "/{user_id}",
    response_model=ProgressListResponse,
    summary="Get user progress",
    description="Retrieve all progress records for a user."
)
async def get_user_progress(
    user_id: str,
    topic: Optional[str] = Query(None, description="Filter by course topic"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty")
):
    """
    Get all progress records for a user.

    Optionally filter by topic and/or difficulty.
    Results are sorted by most recent first.
    """
    try:
        db = MongoDB.get_db()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )

        # Build query
        query = {"user_id": user_id}
        if topic:
            query["course_topic"] = topic.lower().strip()
        if difficulty:
            query["difficulty"] = difficulty

        # Fetch and sort by completed_at descending
        cursor = db[PROGRESS_COLLECTION].find(query).sort("completed_at", -1)
        records = await cursor.to_list(length=100)

        # Convert to response models
        progress_list = []
        for record in records:
            progress_list.append(ProgressResponse(
                user_id=record["user_id"],
                course_topic=record["course_topic"],
                difficulty=record.get("difficulty", "intermediate"),
                chapter_number=record["chapter_number"],
                chapter_title=record.get("chapter_title", f"Chapter {record['chapter_number']}"),
                score=record.get("score", 0.0),
                score_percent=int(record.get("score", 0.0) * 100),
                correct_answers=record.get("correct_answers", 0),
                total_questions=record.get("total_questions", 0),
                completed=record.get("completed", False),
                completed_at=record.get("completed_at"),
                created_at=record.get("started_at")
            ))

        return ProgressListResponse(
            user_id=user_id,
            total_quizzes=len(progress_list),
            progress=progress_list
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch progress: {str(e)}"
        )


@router.get(
    "/{user_id}/summary",
    response_model=ProgressSummary,
    summary="Get user progress summary",
    description="Get an aggregate summary of user's overall progress."
)
async def get_user_summary(user_id: str):
    """
    Get aggregate summary of user's progress across all courses.
    """
    try:
        db = MongoDB.get_db()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )

        # Fetch all user records
        cursor = db[PROGRESS_COLLECTION].find({"user_id": user_id})
        records = await cursor.to_list(length=100)

        if not records:
            return ProgressSummary(
                user_id=user_id,
                total_quizzes_completed=0,
                total_questions_answered=0,
                total_correct=0,
                average_score=0.0,
                courses=[]
            )

        # Calculate aggregates
        total_quizzes = len(records)
        total_questions = sum(r.get("total_questions", 0) for r in records)
        total_correct = sum(r.get("correct_answers", 0) for r in records)
        total_score = sum(r.get("score", 0.0) for r in records)
        average_score = total_score / total_quizzes if total_quizzes > 0 else 0.0

        # Get unique courses
        courses = list(set(r.get("course_topic", "") for r in records))

        return ProgressSummary(
            user_id=user_id,
            total_quizzes_completed=total_quizzes,
            total_questions_answered=total_questions,
            total_correct=total_correct,
            average_score=round(average_score, 2),
            courses=courses
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch summary: {str(e)}"
        )


@router.delete(
    "/{user_id}/{topic}/{chapter_number}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete progress record",
    description="Delete a specific progress record."
)
async def delete_progress(
    user_id: str,
    topic: str,
    chapter_number: int
):
    """
    Delete a specific progress record.

    Useful for allowing users to retry a quiz with fresh state.
    """
    try:
        db = MongoDB.get_db()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )

        result = await db[PROGRESS_COLLECTION].delete_one({
            "user_id": user_id,
            "course_topic": topic.lower().strip(),
            "chapter_number": chapter_number
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Progress record not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete progress: {str(e)}"
        )

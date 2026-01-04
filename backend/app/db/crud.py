"""
CRUD operations for MongoDB collections.
Provides async database operations for courses, questions, and progress.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.connection import MongoDB
from app.db.models import CourseDocument, QuestionDocument, UserProgressDocument
from app.models.course import Chapter


# Collection names
COURSES_COLLECTION = "courses"
QUESTIONS_COLLECTION = "questions"
PROGRESS_COLLECTION = "user_progress"


# =============================================================================
# Course Operations
# =============================================================================

async def save_course(
    topic: str,
    difficulty: str,
    chapters: List[Chapter],
    provider: str
) -> Optional[str]:
    """
    Save a generated course to the database.

    Args:
        topic: The course topic
        difficulty: Difficulty level
        chapters: List of Chapter objects
        provider: AI provider used

    Returns:
        Inserted document ID or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Normalize topic for consistent lookups
    normalized_topic = topic.lower().strip()

    # Convert chapters to dicts
    chapters_data = [chapter.model_dump() for chapter in chapters]

    document = {
        "topic": normalized_topic,
        "original_topic": topic,
        "difficulty": difficulty,
        "chapters": chapters_data,
        "provider": provider,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    # Upsert: update if exists, insert if not
    result = await db[COURSES_COLLECTION].update_one(
        {"topic": normalized_topic, "difficulty": difficulty},
        {"$set": document},
        upsert=True
    )

    return str(result.upserted_id) if result.upserted_id else "updated"


async def get_course_by_topic(
    topic: str,
    difficulty: str
) -> Optional[Dict[str, Any]]:
    """
    Get a cached course by topic and difficulty.

    Args:
        topic: The course topic
        difficulty: Difficulty level

    Returns:
        Course document or None if not found
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    normalized_topic = topic.lower().strip()

    course = await db[COURSES_COLLECTION].find_one({
        "topic": normalized_topic,
        "difficulty": difficulty
    })

    return course


async def get_all_courses() -> List[Dict[str, Any]]:
    """
    Get all cached courses.

    Returns:
        List of course documents
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    cursor = db[COURSES_COLLECTION].find({})
    courses = await cursor.to_list(length=100)

    return courses


async def get_courses_by_ids(course_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get multiple courses by their MongoDB _ids.

    Args:
        course_ids: List of course MongoDB ObjectId strings

    Returns:
        List of course documents
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    if not course_ids:
        return []

    try:
        # Convert string IDs to ObjectId
        object_ids = [ObjectId(cid) for cid in course_ids]

        # Query with $in operator
        cursor = db[COURSES_COLLECTION].find({"_id": {"$in": object_ids}})
        courses = await cursor.to_list(length=100)

        # Add string id field for each course
        for course in courses:
            course["id"] = str(course["_id"])

        return courses
    except Exception:
        return []


async def save_course_for_user(
    user_id: str,
    topic: str,
    difficulty: str,
    complexity_score: Optional[int],
    category: Optional[str],
    chapters: List[Chapter],
    provider: str
) -> Optional[str]:
    """
    Save a course linked to a user.

    Args:
        user_id: The user's ID
        topic: The course topic
        difficulty: Difficulty level
        complexity_score: Topic complexity score
        category: Topic category (official_certification, college_course, etc.)
        chapters: List of Chapter objects
        provider: AI provider used

    Returns:
        Inserted document ID as string, or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Convert chapters to dicts
    chapters_data = [chapter.model_dump() for chapter in chapters]

    document = {
        "user_id": user_id,
        "topic": topic.lower().strip(),
        "original_topic": topic,
        "difficulty": difficulty,
        "complexity_score": complexity_score,
        "category": category,
        "chapters": chapters_data,
        "total_chapters": len(chapters),
        "provider": provider,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await db[COURSES_COLLECTION].insert_one(document)
    return str(result.inserted_id)


async def save_course_from_files(
    user_id: str,
    topic: str,
    difficulty: str,
    complexity_score: Optional[int],
    category: Optional[str],
    chapters: List[Chapter],
    provider: str,
    source_files: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Save a course generated from uploaded files.

    Args:
        user_id: The user's ID
        topic: The course topic (provided or inferred)
        difficulty: Difficulty level
        complexity_score: Topic complexity score
        category: Topic category
        chapters: List of Chapter objects
        provider: AI provider used
        source_files: List of file metadata dicts

    Returns:
        Inserted document ID as string, or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Convert chapters to dicts
    chapters_data = [chapter.model_dump() for chapter in chapters]

    document = {
        "user_id": user_id,
        "topic": topic.lower().strip(),
        "original_topic": topic,
        "difficulty": difficulty,
        "complexity_score": complexity_score,
        "category": category,
        "chapters": chapters_data,
        "total_chapters": len(chapters),
        "provider": provider,
        "source_type": "files",
        "source_files": source_files,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await db[COURSES_COLLECTION].insert_one(document)
    return str(result.inserted_id)


async def get_courses_by_user(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all courses for a user, ordered by created_at descending.

    Args:
        user_id: The user's ID

    Returns:
        List of course documents with id field
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    cursor = db[COURSES_COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
    courses = await cursor.to_list(length=100)

    # Add string id field for each course
    for course in courses:
        course["id"] = str(course["_id"])

    return courses


async def get_course_by_id(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single course by its _id.

    Args:
        course_id: MongoDB ObjectId as string

    Returns:
        Course document with id field, or None if not found
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    try:
        course = await db[COURSES_COLLECTION].find_one({"_id": ObjectId(course_id)})
        if course:
            course["id"] = str(course["_id"])
        return course
    except Exception:
        return None


async def delete_course(course_id: str, user_id: str) -> bool:
    """
    Delete a course if owned by the user.

    Args:
        course_id: MongoDB ObjectId as string
        user_id: The user's ID (must own the course)

    Returns:
        True if deleted, False if not found or not owned
    """
    db = MongoDB.get_db()
    if db is None:
        return False

    try:
        result = await db[COURSES_COLLECTION].delete_one({
            "_id": ObjectId(course_id),
            "user_id": user_id
        })
        return result.deleted_count > 0
    except Exception:
        return False


# =============================================================================
# Question Operations
# =============================================================================

async def save_questions(
    course_topic: str,
    difficulty: str,
    chapter_number: int,
    chapter_title: str,
    mcq: List[Dict[str, Any]],
    true_false: List[Dict[str, Any]],
    provider: str
) -> Optional[str]:
    """
    Save generated questions to the database.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number
        chapter_title: Chapter title
        mcq: Multiple choice questions
        true_false: True/False questions
        provider: AI provider used

    Returns:
        Inserted document ID or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    normalized_topic = course_topic.lower().strip()

    document = {
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "chapter_number": chapter_number,
        "chapter_title": chapter_title,
        "mcq": mcq,
        "true_false": true_false,
        "provider": provider,
        "created_at": datetime.utcnow()
    }

    # Upsert: update if exists, insert if not
    result = await db[QUESTIONS_COLLECTION].update_one(
        {
            "course_topic": normalized_topic,
            "difficulty": difficulty,
            "chapter_number": chapter_number
        },
        {"$set": document},
        upsert=True
    )

    return str(result.upserted_id) if result.upserted_id else "updated"


async def get_questions(
    course_topic: str,
    difficulty: str,
    chapter_number: int
) -> Optional[Dict[str, Any]]:
    """
    Get cached questions for a chapter.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number

    Returns:
        Questions document or None if not found
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    normalized_topic = course_topic.lower().strip()

    questions = await db[QUESTIONS_COLLECTION].find_one({
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "chapter_number": chapter_number
    })

    return questions


# Collection for incremental question batches
QUESTION_BATCHES_COLLECTION = "question_batches"


async def save_question_batch(
    course_topic: str,
    difficulty: str,
    chapter_number: int,
    key_concept: str,
    mcq: List[Dict[str, Any]],
    true_false: List[Dict[str, Any]],
    provider: str
) -> Optional[str]:
    """
    Save a batch of questions for a single key concept.
    Used for incremental question generation.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number
        key_concept: The specific concept these questions cover
        mcq: Multiple choice questions for this concept
        true_false: True/False questions for this concept
        provider: AI provider used

    Returns:
        Inserted document ID or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    normalized_topic = course_topic.lower().strip()
    normalized_concept = key_concept.lower().strip()

    document = {
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "chapter_number": chapter_number,
        "key_concept": normalized_concept,
        "original_concept": key_concept,
        "mcq": mcq,
        "true_false": true_false,
        "provider": provider,
        "created_at": datetime.utcnow()
    }

    # Upsert: update if exists for this concept, insert if not
    result = await db[QUESTION_BATCHES_COLLECTION].update_one(
        {
            "course_topic": normalized_topic,
            "difficulty": difficulty,
            "chapter_number": chapter_number,
            "key_concept": normalized_concept
        },
        {"$set": document},
        upsert=True
    )

    return str(result.upserted_id) if result.upserted_id else "updated"


async def get_question_batches(
    course_topic: str,
    difficulty: str,
    chapter_number: int
) -> List[Dict[str, Any]]:
    """
    Get all question batches for a chapter.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number

    Returns:
        List of question batch documents
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    normalized_topic = course_topic.lower().strip()

    cursor = db[QUESTION_BATCHES_COLLECTION].find({
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "chapter_number": chapter_number
    })

    batches = await cursor.to_list(length=50)
    return batches


async def aggregate_question_batches(
    course_topic: str,
    difficulty: str,
    chapter_number: int,
    chapter_title: str
) -> Optional[Dict[str, Any]]:
    """
    Aggregate all question batches for a chapter into a single document.
    Also saves the aggregated result to the main questions collection.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number
        chapter_title: Chapter title for the aggregated document

    Returns:
        Aggregated questions document or None if no batches found
    """
    batches = await get_question_batches(course_topic, difficulty, chapter_number)

    if not batches:
        return None

    # Aggregate all MCQ and T/F questions from batches
    all_mcq = []
    all_tf = []
    provider = batches[0].get("provider", "unknown") if batches else "unknown"

    for batch in batches:
        all_mcq.extend(batch.get("mcq", []))
        all_tf.extend(batch.get("true_false", []))

    # Save aggregated result to main questions collection
    await save_questions(
        course_topic=course_topic,
        difficulty=difficulty,
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        mcq=all_mcq,
        true_false=all_tf,
        provider=provider
    )

    return {
        "course_topic": course_topic.lower().strip(),
        "difficulty": difficulty,
        "chapter_number": chapter_number,
        "chapter_title": chapter_title,
        "mcq": all_mcq,
        "true_false": all_tf,
        "provider": provider,
        "batches_aggregated": len(batches)
    }


async def delete_question_batches(
    course_topic: str,
    difficulty: str,
    chapter_number: int
) -> int:
    """
    Delete all question batches for a chapter.
    Call this after successful aggregation to clean up.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number

    Returns:
        Number of deleted documents
    """
    db = MongoDB.get_db()
    if db is None:
        return 0

    normalized_topic = course_topic.lower().strip()

    result = await db[QUESTION_BATCHES_COLLECTION].delete_many({
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "chapter_number": chapter_number
    })

    return result.deleted_count


# =============================================================================
# User Progress Operations
# =============================================================================

async def update_progress(
    user_id: str,
    course_topic: str,
    difficulty: str,
    chapter_number: int,
    answer: Dict[str, Any],
    is_correct: bool
) -> Optional[str]:
    """
    Update user progress with a new answer.

    Args:
        user_id: User identifier
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number
        answer: Answer data (question_id, user_answer, etc.)
        is_correct: Whether the answer was correct

    Returns:
        Document ID or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    normalized_topic = course_topic.lower().strip()
    now = datetime.utcnow()

    # Add correctness to the answer
    answer["is_correct"] = is_correct

    # Find existing progress
    existing = await db[PROGRESS_COLLECTION].find_one({
        "user_id": user_id,
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "chapter_number": chapter_number
    })

    if existing:
        # Update existing progress
        new_correct = existing.get("correct_answers", 0) + (1 if is_correct else 0)
        new_total = existing.get("total_questions", 0) + 1
        new_score = new_correct / new_total if new_total > 0 else 0.0

        await db[PROGRESS_COLLECTION].update_one(
            {"_id": existing["_id"]},
            {
                "$push": {"answers": answer},
                "$set": {
                    "correct_answers": new_correct,
                    "total_questions": new_total,
                    "score": new_score,
                    "updated_at": now
                }
            }
        )
        return str(existing["_id"])
    else:
        # Create new progress document
        document = {
            "user_id": user_id,
            "course_topic": normalized_topic,
            "difficulty": difficulty,
            "chapter_number": chapter_number,
            "answers": [answer],
            "score": 1.0 if is_correct else 0.0,
            "total_questions": 1,
            "correct_answers": 1 if is_correct else 0,
            "completed": False,
            "started_at": now,
            "completed_at": None,
            "updated_at": now
        }

        result = await db[PROGRESS_COLLECTION].insert_one(document)
        return str(result.inserted_id)


async def get_user_progress(
    user_id: str,
    course_topic: Optional[str] = None,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get user progress, optionally filtered by course.

    Args:
        user_id: User identifier
        course_topic: Optional topic filter
        difficulty: Optional difficulty filter

    Returns:
        List of progress documents
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    query = {"user_id": user_id}

    if course_topic:
        query["course_topic"] = course_topic.lower().strip()
    if difficulty:
        query["difficulty"] = difficulty

    cursor = db[PROGRESS_COLLECTION].find(query)
    progress = await cursor.to_list(length=100)

    return progress


async def mark_chapter_complete(
    user_id: str,
    course_topic: str,
    difficulty: str,
    chapter_number: int
) -> bool:
    """
    Mark a chapter as completed for a user.

    Args:
        user_id: User identifier
        course_topic: The course topic
        difficulty: Course difficulty level
        chapter_number: Chapter number

    Returns:
        True if updated, False otherwise
    """
    db = MongoDB.get_db()
    if db is None:
        return False

    normalized_topic = course_topic.lower().strip()
    now = datetime.utcnow()

    result = await db[PROGRESS_COLLECTION].update_one(
        {
            "user_id": user_id,
            "course_topic": normalized_topic,
            "difficulty": difficulty,
            "chapter_number": chapter_number
        },
        {
            "$set": {
                "completed": True,
                "completed_at": now,
                "updated_at": now
            }
        }
    )

    return result.modified_count > 0


# =============================================================================
# Document Analysis Operations (Temporary Storage)
# =============================================================================

DOCUMENT_ANALYSES_COLLECTION = "document_analyses"


async def save_document_analysis(
    user_id: str,
    outline: Dict[str, Any],
    raw_content: str,
    source_files: List[Dict[str, Any]],
    expires_in_minutes: int = 30
) -> Optional[str]:
    """
    Save a temporary document analysis for user confirmation.

    The document will have a TTL and expire after the specified time.

    Args:
        user_id: The user's ID
        outline: DocumentOutline as dict
        raw_content: Full extracted text from files
        source_files: List of file metadata dicts
        expires_in_minutes: Time until document expires

    Returns:
        Inserted document ID as string, or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    from datetime import timedelta
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=expires_in_minutes)

    document = {
        "user_id": user_id,
        "outline": outline,
        "raw_content": raw_content,
        "source_files": source_files,
        "created_at": now,
        "expires_at": expires_at
    }

    result = await db[DOCUMENT_ANALYSES_COLLECTION].insert_one(document)

    # Ensure TTL index exists (MongoDB will automatically delete expired docs)
    # This is idempotent - if index exists, it won't create a duplicate
    try:
        await db[DOCUMENT_ANALYSES_COLLECTION].create_index(
            "expires_at",
            expireAfterSeconds=0
        )
    except Exception:
        # Index may already exist
        pass

    return str(result.inserted_id)


async def get_document_analysis(
    analysis_id: str,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a pending document analysis.

    Args:
        analysis_id: The analysis document ID
        user_id: The user's ID (must match for security)

    Returns:
        Analysis document or None if not found/expired
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    try:
        analysis = await db[DOCUMENT_ANALYSES_COLLECTION].find_one({
            "_id": ObjectId(analysis_id),
            "user_id": user_id
        })

        if analysis:
            # Check if expired (in case TTL hasn't cleaned up yet)
            if analysis.get("expires_at") and analysis["expires_at"] < datetime.utcnow():
                return None
            analysis["id"] = str(analysis["_id"])

        return analysis
    except Exception:
        return None


async def delete_document_analysis(analysis_id: str) -> bool:
    """
    Delete a document analysis after processing.

    Args:
        analysis_id: The analysis document ID

    Returns:
        True if deleted, False otherwise
    """
    db = MongoDB.get_db()
    if db is None:
        return False

    try:
        result = await db[DOCUMENT_ANALYSES_COLLECTION].delete_one({
            "_id": ObjectId(analysis_id)
        })
        return result.deleted_count > 0
    except Exception:
        return False

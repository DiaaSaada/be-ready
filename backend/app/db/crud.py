"""
CRUD operations for MongoDB collections.
Provides async database operations for courses, questions, and progress.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
from bson import ObjectId
from app.db.connection import MongoDB
from app.db.models import CourseDocument, QuestionDocument, UserProgressDocument
from app.models.course import Chapter, generate_course_slug


# Collection names
COURSES_COLLECTION = "courses"
QUESTIONS_COLLECTION = "questions"
PROGRESS_COLLECTION = "user_progress"
GAP_QUIZ_CACHE_COLLECTION = "gap_quiz_cache"


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
) -> Optional[Dict[str, str]]:
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
        Dict with 'id' and 'slug', or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Generate unique slug
    slug = generate_course_slug(topic, difficulty)

    # Convert chapters to dicts
    chapters_data = [chapter.model_dump() for chapter in chapters]

    document = {
        "user_id": user_id,
        "slug": slug,
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
    return {"id": str(result.inserted_id), "slug": slug}


async def save_course_from_files(
    user_id: str,
    topic: str,
    difficulty: str,
    complexity_score: Optional[int],
    category: Optional[str],
    chapters: List[Chapter],
    provider: str,
    source_files: List[Dict[str, Any]]
) -> Optional[Dict[str, str]]:
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
        Dict with 'id' and 'slug', or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Generate unique slug
    slug = generate_course_slug(topic, difficulty)

    # Convert chapters to dicts
    chapters_data = [chapter.model_dump() for chapter in chapters]

    document = {
        "user_id": user_id,
        "slug": slug,
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
    return {"id": str(result.inserted_id), "slug": slug}


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


async def get_course_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get a single course by its unique slug.

    Args:
        slug: Unique course slug (e.g., 'python-programming-beginner-a7x3k2')

    Returns:
        Course document with id field, or None if not found
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    try:
        course = await db[COURSES_COLLECTION].find_one({"slug": slug})
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


async def get_question_counts_for_course(
    course_topic: str,
    difficulty: str
) -> Dict[int, int]:
    """
    Get question counts for all chapters of a course.

    Args:
        course_topic: The course topic
        difficulty: Course difficulty level

    Returns:
        Dictionary mapping chapter_number to total question count
    """
    db = MongoDB.get_db()
    if db is None:
        return {}

    normalized_topic = course_topic.lower().strip()

    # Find all question documents for this course
    cursor = db[QUESTIONS_COLLECTION].find({
        "course_topic": normalized_topic,
        "difficulty": difficulty
    })

    counts = {}
    async for doc in cursor:
        chapter_num = doc.get("chapter_number")
        if chapter_num is not None:
            mcq_count = len(doc.get("mcq", []))
            tf_count = len(doc.get("true_false", []))
            counts[chapter_num] = mcq_count + tf_count

    return counts


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


# =============================================================================
# Mentor / Gap Quiz Operations
# =============================================================================

async def get_user_progress_for_course(
    user_id: str,
    course_slug: str
) -> List[Dict[str, Any]]:
    """
    Get all progress records for a user on a specific course (by slug).

    Args:
        user_id: User identifier
        course_slug: Course slug identifier

    Returns:
        List of progress documents with chapter info
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    # First get the course to get topic and difficulty
    course = await get_course_by_slug(course_slug)
    if not course:
        return []

    normalized_topic = course.get("topic", "").lower().strip()
    difficulty = course.get("difficulty", "")

    cursor = db[PROGRESS_COLLECTION].find({
        "user_id": user_id,
        "course_topic": normalized_topic,
        "difficulty": difficulty
    }).sort("chapter_number", 1)

    progress = await cursor.to_list(length=100)

    # Add chapter titles from course
    chapters_by_number = {
        ch.get("number"): ch for ch in course.get("chapters", [])
    }
    for p in progress:
        ch_num = p.get("chapter_number")
        if ch_num in chapters_by_number:
            p["chapter_title"] = chapters_by_number[ch_num].get("title", f"Chapter {ch_num}")
        else:
            p["chapter_title"] = f"Chapter {ch_num}"

    return progress


async def get_wrong_answers_for_course(
    user_id: str,
    course_slug: str
) -> List[Dict[str, Any]]:
    """
    Get all wrong answers for a user on a specific course.

    Args:
        user_id: User identifier
        course_slug: Course slug identifier

    Returns:
        List of wrong answer dicts with question details and chapter info
    """
    db = MongoDB.get_db()
    if db is None:
        return []

    # Get the course
    course = await get_course_by_slug(course_slug)
    if not course:
        return []

    normalized_topic = course.get("topic", "").lower().strip()
    difficulty = course.get("difficulty", "")

    # Get all progress for this user/course
    cursor = db[PROGRESS_COLLECTION].find({
        "user_id": user_id,
        "course_topic": normalized_topic,
        "difficulty": difficulty
    })

    progress_docs = await cursor.to_list(length=100)

    # Consolidate by chapter - keep latest attempt per chapter only
    chapter_progress = {}
    for p in progress_docs:
        chapter_num = p.get("chapter_number")
        existing = chapter_progress.get(chapter_num)
        if existing is None or str(p.get("_id", "")) > str(existing.get("_id", "")):
            chapter_progress[chapter_num] = p

    # Build chapter lookup
    chapters_by_number = {
        ch.get("number"): ch for ch in course.get("chapters", [])
    }

    # Collect wrong answers from latest attempt per chapter only
    wrong_answers_by_qid = {}  # question_id -> answer info (deduplicates automatically)

    for prog in chapter_progress.values():
        chapter_num = prog.get("chapter_number")
        chapter_title = chapters_by_number.get(chapter_num, {}).get("title", f"Chapter {chapter_num}")

        for ans in prog.get("answers", []):
            if not ans.get("is_correct", True):  # Wrong answer
                qid = ans.get("question_id")
                if qid:
                    wrong_answers_by_qid[qid] = {
                        "user_answer": ans.get("selected"),  # Field is 'selected' in AnswerRecord model
                        "chapter_number": chapter_num,
                        "chapter_title": chapter_title
                    }

    if not wrong_answers_by_qid:
        return []

    # Get questions from the questions collection to get full question details
    questions_cursor = db[QUESTIONS_COLLECTION].find({
        "course_topic": normalized_topic,
        "difficulty": difficulty
    })

    question_docs = await questions_cursor.to_list(length=100)

    # Build question lookup by ID
    questions_by_id = {}
    for doc in question_docs:
        for q in doc.get("mcq", []):
            questions_by_id[q.get("id")] = {
                **q,
                "question_type": "mcq"
            }
        for q in doc.get("true_false", []):
            questions_by_id[q.get("id")] = {
                **q,
                "question_type": "true_false"
            }

    # Build wrong answers with full details
    wrong_answers = []
    for qid in wrong_answers_by_qid:
        if qid in questions_by_id:
            q = questions_by_id[qid]
            ans_info = wrong_answers_by_qid[qid]
            wrong_answers.append({
                "question_id": qid,
                "question_text": q.get("question_text", ""),
                "question_type": q.get("question_type", "mcq"),
                "options": q.get("options"),  # None for true_false
                "user_answer": ans_info["user_answer"],
                "correct_answer": q.get("correct_answer"),
                "explanation": q.get("explanation", ""),
                "chapter_number": ans_info["chapter_number"],
                "chapter_title": ans_info["chapter_title"],
                "hint": None  # Hints added by analyzer if requested
            })

    return wrong_answers


async def get_completed_chapters_count(
    user_id: str,
    course_slug: str
) -> int:
    """
    Get the number of completed chapters for a user on a course.

    Args:
        user_id: User identifier
        course_slug: Course slug identifier

    Returns:
        Number of completed chapters
    """
    db = MongoDB.get_db()
    if db is None:
        return 0

    # Get the course
    course = await get_course_by_slug(course_slug)
    if not course:
        return 0

    normalized_topic = course.get("topic", "").lower().strip()
    difficulty = course.get("difficulty", "")

    count = await db[PROGRESS_COLLECTION].count_documents({
        "user_id": user_id,
        "course_topic": normalized_topic,
        "difficulty": difficulty,
        "completed": True
    })

    return count


async def get_course_stats_for_mentor(
    user_id: str,
    course_slug: str
) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive course stats for mentor analysis.

    Args:
        user_id: User identifier
        course_slug: Course slug identifier

    Returns:
        Dict with course info, progress stats, and weak areas
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Get the course
    course = await get_course_by_slug(course_slug)
    if not course:
        return None

    normalized_topic = course.get("topic", "").lower().strip()
    difficulty = course.get("difficulty", "")

    # Get all progress for this user/course
    progress_list = await get_user_progress_for_course(user_id, course_slug)

    # Consolidate by chapter_number - keep only the latest attempt per chapter
    # Progress list is sorted by chapter_number, but we need latest per chapter
    # MongoDB _id is time-based, so larger _id = more recent
    chapter_progress = {}
    for p in progress_list:
        chapter_num = p.get("chapter_number")
        existing = chapter_progress.get(chapter_num)
        if existing is None:
            chapter_progress[chapter_num] = p
        else:
            # Keep the one with larger _id (more recent)
            if p.get("_id", "") > existing.get("_id", ""):
                chapter_progress[chapter_num] = p

    consolidated_progress = list(chapter_progress.values())

    # Calculate stats using consolidated progress (one entry per chapter)
    total_chapters = course.get("total_chapters", len(course.get("chapters", [])))
    completed_chapters = sum(1 for p in consolidated_progress if p.get("completed"))
    total_correct = sum(p.get("correct_answers", 0) for p in consolidated_progress)
    total_questions = sum(p.get("total_questions", 0) for p in consolidated_progress)
    average_score = total_correct / total_questions if total_questions > 0 else 0.0

    # Get wrong answers
    wrong_answers = await get_wrong_answers_for_course(user_id, course_slug)

    return {
        "course_slug": course_slug,
        "course_topic": course.get("original_topic", course.get("topic")),
        "difficulty": difficulty,
        "total_chapters": total_chapters,
        "completed_chapters": completed_chapters,
        "average_score": average_score,
        "total_correct": total_correct,
        "total_questions": total_questions,
        "total_wrong_answers": len(wrong_answers),
        "progress_by_chapter": consolidated_progress,
        "chapters": course.get("chapters", [])
    }


# =============================================================================
# Gap Quiz Cache Operations
# =============================================================================

def compute_weak_areas_hash(weak_areas: List[Dict[str, Any]]) -> str:
    """
    Create hash from weak area chapters and scores for cache key.
    Cache invalidates when user's weak areas change.

    Args:
        weak_areas: List of weak area dicts with chapter_number and score

    Returns:
        MD5 hash string
    """
    # Extract (chapter_number, rounded_score) tuples
    data = []
    for wa in weak_areas:
        ch = wa.get("chapter_number") if isinstance(wa, dict) else wa.chapter_number
        score = wa.get("score", 0) if isinstance(wa, dict) else wa.score
        data.append((ch, round(score, 2)))

    # Sort for consistency and hash
    return hashlib.md5(str(sorted(data)).encode()).hexdigest()


async def get_cached_gap_quiz(
    user_id: str,
    course_slug: str,
    weak_areas_hash: str,
    include_hints: bool
) -> Optional[List[Dict[str, Any]]]:
    """
    Get cached extra questions if hash matches and hints requirement met.

    Args:
        user_id: User identifier
        course_slug: Course slug
        weak_areas_hash: Hash of current weak areas
        include_hints: Whether hints are needed

    Returns:
        List of cached questions or None if cache miss
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    query = {
        "user_id": user_id,
        "course_slug": course_slug,
        "weak_areas_hash": weak_areas_hash
    }

    # If hints are needed, only accept cached with hints
    if include_hints:
        query["include_hints"] = True

    cached = await db[GAP_QUIZ_CACHE_COLLECTION].find_one(query)

    if cached:
        return cached.get("extra_questions", [])

    return None


async def save_gap_quiz_cache(
    user_id: str,
    course_slug: str,
    weak_areas_hash: str,
    extra_questions: List[Dict[str, Any]],
    include_hints: bool,
    provider: str
) -> Optional[str]:
    """
    Save AI-generated questions to cache.

    Args:
        user_id: User identifier
        course_slug: Course slug
        weak_areas_hash: Hash of weak areas (cache key)
        extra_questions: List of question dicts
        include_hints: Whether hints are included
        provider: AI provider that generated these

    Returns:
        Inserted document ID or None
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    # Convert GapQuizQuestion objects to dicts if needed
    questions_data = []
    for q in extra_questions:
        if hasattr(q, 'model_dump'):
            questions_data.append(q.model_dump())
        elif isinstance(q, dict):
            questions_data.append(q)

    document = {
        "user_id": user_id,
        "course_slug": course_slug,
        "weak_areas_hash": weak_areas_hash,
        "extra_questions": questions_data,
        "include_hints": include_hints,
        "provider": provider,
        "created_at": datetime.utcnow()
    }

    # Upsert: replace existing cache for same user/course/hash
    result = await db[GAP_QUIZ_CACHE_COLLECTION].update_one(
        {
            "user_id": user_id,
            "course_slug": course_slug,
            "weak_areas_hash": weak_areas_hash
        },
        {"$set": document},
        upsert=True
    )

    return str(result.upserted_id) if result.upserted_id else "updated"


async def invalidate_gap_quiz_cache(
    user_id: str,
    course_slug: str
) -> int:
    """
    Delete all cached quizzes for a user/course.
    Called when user explicitly wants fresh generation.

    Args:
        user_id: User identifier
        course_slug: Course slug

    Returns:
        Number of deleted documents
    """
    db = MongoDB.get_db()
    if db is None:
        return 0

    result = await db[GAP_QUIZ_CACHE_COLLECTION].delete_many({
        "user_id": user_id,
        "course_slug": course_slug
    })

    return result.deleted_count


# =============================================================================
# Question Pool Enhancement
# =============================================================================

async def add_gap_quiz_questions_to_chapters(
    course_topic: str,
    difficulty: str,
    extra_questions: List[Any]
) -> int:
    """
    Add gap quiz extra questions to chapter question pools.
    This allows AI-generated gap quiz questions to be reused in regular quizzes.

    Args:
        course_topic: Course topic
        difficulty: Course difficulty
        extra_questions: List of GapQuizQuestion objects

    Returns:
        Number of questions added
    """
    db = MongoDB.get_db()
    if db is None:
        return 0

    if not extra_questions:
        return 0

    # Group questions by source_chapter
    by_chapter: Dict[int, Dict[str, List[Dict]]] = {}
    for q in extra_questions:
        # Handle both GapQuizQuestion objects and dicts
        if hasattr(q, 'source_chapter'):
            ch = q.source_chapter
            q_type = q.question_type
            q_dict = {
                "id": q.id,
                "question_text": q.question_text,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "source": "gap_quiz",
                "target_concept": q.target_concept
            }
            if q_type == "mcq":
                q_dict["options"] = q.options
        else:
            ch = q.get("source_chapter")
            q_type = q.get("question_type", "mcq")
            q_dict = {
                "id": q.get("id"),
                "question_text": q.get("question_text"),
                "correct_answer": q.get("correct_answer"),
                "explanation": q.get("explanation"),
                "difficulty": q.get("difficulty"),
                "source": "gap_quiz",
                "target_concept": q.get("target_concept")
            }
            if q_type == "mcq":
                q_dict["options"] = q.get("options")

        if ch not in by_chapter:
            by_chapter[ch] = {"mcq": [], "true_false": []}

        if q_type == "mcq":
            by_chapter[ch]["mcq"].append(q_dict)
        else:
            by_chapter[ch]["true_false"].append(q_dict)

    # Append to each chapter's question document
    added = 0
    normalized_topic = course_topic.lower().strip()

    for chapter_num, questions in by_chapter.items():
        update_ops = {}
        if questions["mcq"]:
            update_ops["mcq"] = {"$each": questions["mcq"]}
        if questions["true_false"]:
            update_ops["true_false"] = {"$each": questions["true_false"]}

        if update_ops:
            await db[QUESTIONS_COLLECTION].update_one(
                {
                    "course_topic": normalized_topic,
                    "difficulty": difficulty,
                    "chapter_number": chapter_num
                },
                {"$push": update_ops}
            )
            added += len(questions["mcq"]) + len(questions["true_false"])

    return added

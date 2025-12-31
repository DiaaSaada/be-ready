"""
User CRUD operations for MongoDB.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from app.db.connection import MongoDB


USERS_COLLECTION = "users"


async def create_user(
    name: str,
    email: str,
    hashed_password: str
) -> Optional[str]:
    """
    Create a new user in the database.

    Args:
        name: User's display name
        email: User's email address
        hashed_password: Bcrypt hashed password

    Returns:
        Inserted document ID or None if DB not connected
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    document = {
        "name": name,
        "email": email.lower().strip(),
        "hashed_password": hashed_password,
        "enrolled_courses": [],
        "created_at": datetime.utcnow()
    }

    result = await db[USERS_COLLECTION].insert_one(document)
    return str(result.inserted_id)


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email address.

    Args:
        email: User's email address

    Returns:
        User document or None if not found
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    user = await db[USERS_COLLECTION].find_one({
        "email": email.lower().strip()
    })

    if user:
        user["id"] = str(user["_id"])
        del user["_id"]

    return user


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user by ID.

    Args:
        user_id: MongoDB ObjectId as string

    Returns:
        User document or None if not found
    """
    db = MongoDB.get_db()
    if db is None:
        return None

    try:
        user = await db[USERS_COLLECTION].find_one({
            "_id": ObjectId(user_id)
        })
    except Exception:
        return None

    if user:
        user["id"] = str(user["_id"])
        del user["_id"]

    return user


async def email_exists(email: str) -> bool:
    """
    Check if email is already registered.

    Args:
        email: Email address to check

    Returns:
        True if email exists, False otherwise
    """
    user = await get_user_by_email(email)
    return user is not None


# =============================================================================
# Course Enrollment Operations
# =============================================================================

async def enroll_user_in_course(user_id: str, course_id: str) -> bool:
    """
    Add course to user's enrolled_courses list.

    Args:
        user_id: MongoDB ObjectId as string
        course_id: Course MongoDB ObjectId as string

    Returns:
        True if newly enrolled, False if already enrolled or DB error
    """
    db = MongoDB.get_db()
    if db is None:
        return False

    try:
        # Use $addToSet to add only if not already in array
        result = await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"enrolled_courses": course_id}}
        )
        # modified_count > 0 means the course was added (wasn't already there)
        return result.modified_count > 0
    except Exception:
        return False


async def get_user_enrolled_courses(user_id: str) -> List[str]:
    """
    Get list of course IDs user is enrolled in.

    Args:
        user_id: MongoDB ObjectId as string

    Returns:
        List of course IDs or empty list if not found
    """
    user = await get_user_by_id(user_id)
    if user is None:
        return []
    return user.get("enrolled_courses", [])


async def unenroll_user_from_course(user_id: str, course_id: str) -> bool:
    """
    Remove course from user's enrolled_courses.

    Args:
        user_id: MongoDB ObjectId as string
        course_id: Course MongoDB ObjectId as string

    Returns:
        True if removed, False if wasn't enrolled or DB error
    """
    db = MongoDB.get_db()
    if db is None:
        return False

    try:
        # Use $pull to remove course_id from array
        result = await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"enrolled_courses": course_id}}
        )
        # modified_count > 0 means the course was removed (was in array)
        return result.modified_count > 0
    except Exception:
        return False


async def is_user_enrolled(user_id: str, course_id: str) -> bool:
    """
    Check if user is enrolled in a course.

    Args:
        user_id: MongoDB ObjectId as string
        course_id: Course MongoDB ObjectId as string

    Returns:
        True if enrolled, False otherwise
    """
    db = MongoDB.get_db()
    if db is None:
        return False

    try:
        # Query for user with course_id in enrolled_courses array
        user = await db[USERS_COLLECTION].find_one({
            "_id": ObjectId(user_id),
            "enrolled_courses": course_id
        })
        return user is not None
    except Exception:
        return False

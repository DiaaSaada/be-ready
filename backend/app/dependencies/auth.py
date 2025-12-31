"""
Authentication dependencies for FastAPI route protection.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.services.auth_service import decode_access_token
from app.db.user_repository import get_user_by_id
from app.models.user import UserInDB


# HTTP Bearer scheme for extracting JWT from Authorization header
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    Dependency to get the current authenticated user.

    Extracts JWT from Authorization header, validates it,
    and returns the user from the database.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        UserInDB object for the authenticated user

    Raises:
        HTTPException 401: If token is missing, invalid, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return UserInDB(**user)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
) -> Optional[UserInDB]:
    """
    Optional authentication dependency.
    Returns None if not authenticated instead of raising an exception.

    Useful for endpoints that work for both authenticated and guest users.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        UserInDB object if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

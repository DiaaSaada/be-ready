"""
Authentication API Router.
Handles signup, login, and user info endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    UserInDB
)
from app.db import user_repository
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.dependencies.auth import get_current_user


router = APIRouter()


@router.post(
    "/signup",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with name, email, and password."
)
async def signup(user: UserCreate):
    """
    Register a new user.

    Args:
        user: User registration data (name, email, password)

    Returns:
        JWT access token

    Raises:
        HTTPException 400: If email already exists
        HTTPException 500: If database operation fails
    """
    try:
        # Check if email already exists
        if await user_repository.email_exists(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password and create user
        hashed_password = hash_password(user.password)
        user_id = await user_repository.create_user(
            name=user.name,
            email=user.email,
            hashed_password=hashed_password
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user. Database may be unavailable."
            )

        # Create access token
        access_token = create_access_token(
            data={"user_id": user_id, "email": user.email}
        )

        return Token(access_token=access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup error: {str(e)}"
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Login user",
    description="Authenticate user with email and password."
)
async def login(credentials: UserLogin):
    """
    Authenticate a user and return JWT token.

    Args:
        credentials: Login credentials (email, password)

    Returns:
        JWT access token

    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Get user by email
    user = await user_repository.get_user_by_email(credentials.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(
        data={"user_id": user["id"], "email": user["email"]}
    )

    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information."
)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current user information.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        User data (id, name, email, created_at)
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at
    )

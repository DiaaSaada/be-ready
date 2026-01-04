"""
Token usage tracking API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from app.dependencies.auth import get_current_user
from app.models.user import UserInDB
from app.models.token_usage import TokenUsageResponse, TokenUsageSummary
from app.db import token_repository


router = APIRouter(prefix="/api/v1/tokens", tags=["tokens"])


@router.get("/usage", response_model=TokenUsageResponse)
async def get_token_usage(
    current_user: UserInDB = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip")
):
    """
    Get paginated token usage history for the current user.

    Returns a list of token usage records with totals.
    """
    return await token_repository.get_user_token_usage(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )


@router.get("/usage/summary", response_model=TokenUsageSummary)
async def get_token_summary(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get aggregated token usage summary for the current user.

    Returns breakdowns by operation type and AI provider.
    """
    return await token_repository.get_user_token_summary(user_id=current_user.id)

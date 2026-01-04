"""
Token usage CRUD operations for MongoDB.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.connection import MongoDB
from app.models.token_usage import (
    TokenUsageRecord,
    TokenUsageInDB,
    TokenUsageResponse,
    TokenUsageSummary,
    OperationType
)


TOKEN_USAGE_COLLECTION = "token_usage"


async def ensure_indexes():
    """Create indexes for efficient querying."""
    db = MongoDB.get_db()
    if db is None:
        return

    collection = db[TOKEN_USAGE_COLLECTION]
    # Index on user_id for filtering by user
    await collection.create_index("user_id")
    # Compound index for user + time sorting
    await collection.create_index([("user_id", 1), ("created_at", -1)])


async def save_token_usage(record: TokenUsageRecord) -> Optional[str]:
    """
    Save a token usage record to the database.

    Args:
        record: TokenUsageRecord with usage details

    Returns:
        Inserted document ID or None if DB not connected
    """
    print(f"[TOKEN_REPO] save_token_usage called - operation={record.operation}, user_id={record.user_id}")
    db = MongoDB.get_db()
    if db is None:
        print(f"[TOKEN_REPO] ERROR: MongoDB not connected! Cannot save token usage.")
        return None

    print(f"[TOKEN_REPO] DB connected, preparing document...")
    document = {
        "user_id": record.user_id,
        "operation": record.operation.value if isinstance(record.operation, OperationType) else record.operation,
        "provider": record.provider,
        "model": record.model,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "total_tokens": record.total_tokens,
        "context": record.context,
        "course_id": record.course_id,
        "created_at": record.created_at or datetime.utcnow()
    }

    print(f"[TOKEN_REPO] Inserting document into {TOKEN_USAGE_COLLECTION}...")
    try:
        result = await db[TOKEN_USAGE_COLLECTION].insert_one(document)
        print(f"[TOKEN_REPO] Successfully inserted with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"[TOKEN_REPO] ERROR inserting document: {e}")
        return None


async def get_user_token_usage(
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> TokenUsageResponse:
    """
    Get paginated token usage history for a user.

    Args:
        user_id: MongoDB ObjectId as string
        limit: Number of records to return
        offset: Number of records to skip

    Returns:
        TokenUsageResponse with records and totals
    """
    db = MongoDB.get_db()
    if db is None:
        return TokenUsageResponse(
            records=[],
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            total_records=0,
            limit=limit,
            offset=offset
        )

    collection = db[TOKEN_USAGE_COLLECTION]

    # Get total count
    total_records = await collection.count_documents({"user_id": user_id})

    # Get paginated records (newest first)
    cursor = collection.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)

    # Convert to TokenUsageInDB
    records = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        records.append(TokenUsageInDB(**doc))

    # Get totals using aggregation
    totals_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_input_tokens": {"$sum": "$input_tokens"},
            "total_output_tokens": {"$sum": "$output_tokens"},
            "total_tokens": {"$sum": "$total_tokens"}
        }}
    ]

    totals_cursor = collection.aggregate(totals_pipeline)
    totals_list = await totals_cursor.to_list(length=1)

    if totals_list:
        totals = totals_list[0]
        total_input = totals.get("total_input_tokens", 0)
        total_output = totals.get("total_output_tokens", 0)
        total = totals.get("total_tokens", 0)
    else:
        total_input = 0
        total_output = 0
        total = 0

    return TokenUsageResponse(
        records=records,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total,
        total_records=total_records,
        limit=limit,
        offset=offset
    )


async def get_user_token_summary(user_id: str) -> TokenUsageSummary:
    """
    Get aggregated token usage summary for a user.

    Args:
        user_id: MongoDB ObjectId as string

    Returns:
        TokenUsageSummary with breakdowns by operation and provider
    """
    db = MongoDB.get_db()
    if db is None:
        return TokenUsageSummary()

    collection = db[TOKEN_USAGE_COLLECTION]

    # Aggregate by operation
    operation_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$operation",
            "total_tokens": {"$sum": "$total_tokens"}
        }}
    ]

    op_cursor = collection.aggregate(operation_pipeline)
    op_list = await op_cursor.to_list(length=100)
    by_operation = {item["_id"]: item["total_tokens"] for item in op_list}

    # Aggregate by provider
    provider_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$provider",
            "total_tokens": {"$sum": "$total_tokens"}
        }}
    ]

    prov_cursor = collection.aggregate(provider_pipeline)
    prov_list = await prov_cursor.to_list(length=100)
    by_provider = {item["_id"]: item["total_tokens"] for item in prov_list}

    # Get overall totals
    totals_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_input_tokens": {"$sum": "$input_tokens"},
            "total_output_tokens": {"$sum": "$output_tokens"},
            "total_tokens": {"$sum": "$total_tokens"},
            "record_count": {"$sum": 1}
        }}
    ]

    totals_cursor = collection.aggregate(totals_pipeline)
    totals_list = await totals_cursor.to_list(length=1)

    if totals_list:
        totals = totals_list[0]
        return TokenUsageSummary(
            by_operation=by_operation,
            by_provider=by_provider,
            total_input_tokens=totals.get("total_input_tokens", 0),
            total_output_tokens=totals.get("total_output_tokens", 0),
            total_tokens=totals.get("total_tokens", 0),
            record_count=totals.get("record_count", 0)
        )

    return TokenUsageSummary(
        by_operation=by_operation,
        by_provider=by_provider
    )

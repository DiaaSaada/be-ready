"""
MongoDB Utility Script
Query and inspect MongoDB collections for the AI Learning Platform.

Usage:
    python scripts/check_mongodb.py              # List all collections
    python scripts/check_mongodb.py courses      # Show courses collection
    python scripts/check_mongodb.py questions    # Show questions collection
    python scripts/check_mongodb.py --all        # Show all documents in all collections
"""
import asyncio
import sys
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Load settings from .env or use defaults
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ai_learning_platform")
except ImportError:
    MONGODB_URL = "mongodb://localhost:27017"
    MONGODB_DB_NAME = "ai_learning_platform"


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB documents."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


async def list_collections():
    """List all collections with document counts."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print(f"\n{'='*60}")
    print(f"Database: {MONGODB_DB_NAME}")
    print(f"{'='*60}\n")

    collections = await db.list_collection_names()

    if not collections:
        print("No collections found.")
    else:
        print(f"{'Collection':<25} {'Documents':>10}")
        print(f"{'-'*25} {'-'*10}")

        for coll_name in sorted(collections):
            count = await db[coll_name].count_documents({})
            print(f"{coll_name:<25} {count:>10}")

    print()
    client.close()


async def show_collection(collection_name: str, limit: int = 5):
    """Show documents from a specific collection."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    count = await db[collection_name].count_documents({})

    print(f"\n{'='*60}")
    print(f"Collection: {collection_name} ({count} documents)")
    print(f"{'='*60}\n")

    cursor = db[collection_name].find().limit(limit)
    docs = await cursor.to_list(length=limit)

    for i, doc in enumerate(docs, 1):
        print(f"--- Document {i} ---")
        print(json.dumps(doc, indent=2, cls=JSONEncoder))
        print()

    if count > limit:
        print(f"... and {count - limit} more documents")

    client.close()


async def show_all_collections():
    """Show sample documents from all collections."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    collections = await db.list_collection_names()

    for coll_name in sorted(collections):
        await show_collection(coll_name, limit=2)

    client.close()


async def main():
    args = sys.argv[1:]

    if not args:
        await list_collections()
    elif args[0] == "--all":
        await show_all_collections()
    else:
        collection_name = args[0]
        limit = int(args[1]) if len(args) > 1 else 5
        await show_collection(collection_name, limit)


if __name__ == "__main__":
    asyncio.run(main())

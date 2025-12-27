"""
Main FastAPI application entry point.
This is the core of the AI Learning Platform backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.db.connection import MongoDB


# Create uploads directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)


# OpenAPI Tags Metadata
tags_metadata = [
    {
        "name": "health",
        "description": "Health check and status endpoints.",
    },
    {
        "name": "courses",
        "description": "**Course Generation** - Create AI-powered courses from topics. "
                       "Includes topic validation, chapter generation, and course configuration.",
    },
    {
        "name": "questions",
        "description": "**Question Generation** - Generate MCQ and True/False questions for chapters. "
                       "Features AI-based question count analysis and difficulty-aware generation.",
    },
]


# App description for docs
APP_DESCRIPTION = """
## AI Learning Platform API

An AI-powered learning platform that generates personalized courses and assessments.

### Features

* **Topic Validation** - Validates topics before course generation
* **Course Generation** - Creates structured chapters from any topic
* **Question Generation** - Generates MCQ and True/False questions
* **Multiple AI Providers** - Supports Claude, OpenAI, and Mock providers
* **Difficulty Levels** - Beginner, Intermediate, and Advanced content

### Quick Start

1. **Validate a topic**: `POST /api/v1/courses/validate`
2. **Generate a course**: `POST /api/v1/courses/generate`
3. **Generate questions**: `POST /api/v1/questions/generate`

### AI Providers

Use the `?provider=` query parameter to select:
- `mock` - Fast testing without API calls
- `claude` - Anthropic Claude (default)
- `openai` - OpenAI GPT

### Difficulty Levels

| Level | Audience | Questions |
|-------|----------|-----------|
| `beginner` | Teens, simple language | 8 MCQ, 5 T/F |
| `intermediate` | College students | 12 MCQ, 6 T/F |
| `advanced` | Professionals | 20 MCQ, 8 T/F |
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    print("\n" + "="*70)
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print("="*70)
    print(f"   Upload directory: {settings.upload_dir}")
    print(f"   Database: {settings.mongodb_db_name}")

    # Connect to MongoDB
    await MongoDB.connect()

    print(f"\n   AI Configuration:")
    print(f"   Provider: {settings.default_ai_provider}")
    print(f"   Chapter Gen: {settings.model_chapter_generation}")
    print(f"   Question Gen: {settings.model_question_generation}")
    print(f"   Answer Check: {settings.model_answer_checking}")
    print("="*70 + "\n")

    yield

    # Shutdown
    await MongoDB.disconnect()
    print(f"Shutting down {settings.app_name}")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "AI Learning Platform",
        "url": "https://github.com/your-repo/be-ready",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["health"],
    summary="Welcome",
    description="Root endpoint returning app info and status."
)
async def root():
    """Root endpoint - returns app info and running status."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Health Check",
    description="Returns health status including database connection state."
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        - status: "healthy" if all systems operational
        - app_name: Application name
        - version: Current version
        - database: MongoDB connection status
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "database": "connected" if MongoDB.is_connected() else "disconnected"
    }


# Import routers
from app.routers import courses, questions

# Include routers
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["questions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
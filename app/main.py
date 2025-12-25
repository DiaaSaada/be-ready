"""
Main FastAPI application entry point.
This is the core of the AI Learning Platform backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import settings


# Create uploads directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📁 Upload directory: {settings.upload_dir}")
    print(f"🤖 Default LLM: {settings.default_llm_model}")
    
    # Here we'll add database connection later
    
    yield
    
    # Shutdown
    print(f"👋 Shutting down {settings.app_name}")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered learning platform with adaptive mentoring",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# We'll add routers here later
# app.include_router(courses.router, prefix="/api/v1", tags=["courses"])
# app.include_router(progress.router, prefix="/api/v1", tags=["progress"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
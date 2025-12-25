"""
Application configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: Optional[str] = None
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ai_learning_platform"
    
    # Application Settings
    app_name: str = "AI Learning Platform"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # File Upload
    max_upload_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads"
    
    # AI Settings
    default_llm_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
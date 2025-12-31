"""
Application configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum


class AIProvider(str, Enum):
    """Available AI providers."""
    CLAUDE = "claude"
    OPENAI = "openai"
    MOCK = "mock"


class AIModel(str, Enum):
    """Available AI models."""
    # Claude models (format: claude-{major}-{minor}-{variant}-{date})
    CLAUDE_OPUS_4 = "claude-opus-4-20250514"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    CLAUDE_HAIKU_35 = "claude-3-5-haiku-20241022"
    
    # OpenAI models
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"
    
    # Mock
    MOCK = "mock"


class UseCase(str, Enum):
    """Different use cases for AI services."""
    CHAPTER_GENERATION = "chapter_generation"
    QUESTION_GENERATION = "question_generation"
    QUESTION_COUNT_ANALYSIS = "question_count_analysis"
    STUDENT_FEEDBACK = "student_feedback"
    ANSWER_CHECKING = "answer_checking"
    RAG_QUERY = "rag_query"
    TOPIC_VALIDATION = "topic_validation"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: Optional[str] = None

    # Clerk Authentication
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""
    frontend_url: str = "http://localhost:5173"

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
    
    # AI Provider Selection (for A/B testing)
    # Options: "claude", "openai", "mock"
    default_ai_provider: str = "claude"
    
    # AI Model Configuration per Use Case
    # These can be changed for A/B testing different models
    model_chapter_generation: str = "claude-sonnet-4-20250514"
    model_question_generation: str = "claude-3-5-haiku-20241022"
    model_question_count_analysis: str = "claude-3-5-haiku-20241022"
    model_student_feedback: str = "claude-sonnet-4-20250514"
    model_answer_checking: str = "claude-3-5-haiku-20241022"
    model_rag_query: str = "claude-3-5-haiku-20241022"
    model_topic_validation: str = "claude-3-5-haiku-20241022"
    
    # AI Settings
    max_tokens_chapter: int = 4000
    max_tokens_question: int = 8000
    max_tokens_question_count: int = 300
    max_tokens_feedback: int = 1500
    max_tokens_answer: int = 500
    max_tokens_rag: int = 1000
    max_tokens_validation: int = 500
    
    temperature: float = 0.7
    
    # A/B Testing Configuration
    enable_ab_testing: bool = False
    ab_test_percentage: float = 0.5  # 50% of requests use alternative model
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=('settings_',)
    )
    
    def get_model_for_use_case(self, use_case: UseCase) -> str:
        """
        Get the AI model to use for a specific use case.
        
        Args:
            use_case: The use case (chapter generation, questions, etc.)
            
        Returns:
            Model identifier string
        """
        use_case_map = {
            UseCase.CHAPTER_GENERATION: self.model_chapter_generation,
            UseCase.QUESTION_GENERATION: self.model_question_generation,
            UseCase.QUESTION_COUNT_ANALYSIS: self.model_question_count_analysis,
            UseCase.STUDENT_FEEDBACK: self.model_student_feedback,
            UseCase.ANSWER_CHECKING: self.model_answer_checking,
            UseCase.RAG_QUERY: self.model_rag_query,
            UseCase.TOPIC_VALIDATION: self.model_topic_validation,
        }
        return use_case_map.get(use_case, self.model_chapter_generation)
    
    def get_provider_for_model(self, model: str) -> str:
        """
        Determine which provider to use based on the model name.
        
        Args:
            model: Model identifier string
            
        Returns:
            Provider name (claude, openai, mock)
        """
        if model == "mock":
            return "mock"
        elif model.startswith("claude"):
            return "claude"
        elif model.startswith("gpt"):
            return "openai"
        else:
            return self.default_ai_provider
    
    def get_max_tokens_for_use_case(self, use_case: UseCase) -> int:
        """
        Get max tokens for a specific use case.
        
        Args:
            use_case: The use case
            
        Returns:
            Maximum number of tokens
        """
        use_case_map = {
            UseCase.CHAPTER_GENERATION: self.max_tokens_chapter,
            UseCase.QUESTION_GENERATION: self.max_tokens_question,
            UseCase.QUESTION_COUNT_ANALYSIS: self.max_tokens_question_count,
            UseCase.STUDENT_FEEDBACK: self.max_tokens_feedback,
            UseCase.ANSWER_CHECKING: self.max_tokens_answer,
            UseCase.RAG_QUERY: self.max_tokens_rag,
            UseCase.TOPIC_VALIDATION: self.max_tokens_validation,
        }
        return use_case_map.get(use_case, 2000)


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
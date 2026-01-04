"""
AI Service Factory
Routes requests to the correct AI provider (Claude, OpenAI, Gemini, or Mock).
This is the main entry point for all AI operations.
"""
from typing import Optional
from app.services.base_ai_service import BaseAIService
from app.services.claude_ai_service import ClaudeAIService
from app.services.openai_ai_service import OpenAIService
from app.services.gemini_ai_service import GeminiAIService
from app.services.mock_ai_service import MockAIService
from app.config import settings, UseCase


class AIServiceFactory:
    """
    Factory class that creates and manages AI service instances.
    Handles provider selection based on configuration.
    """
    
    _instances = {}  # Cache service instances
    
    @classmethod
    def get_service(
        cls, 
        use_case: UseCase,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> BaseAIService:
        """
        Get the appropriate AI service for a use case.
        
        Args:
            use_case: The use case (chapter_generation, question_generation, etc.)
            provider_override: Optional provider override for testing ("claude", "openai", "mock")
            model_override: Optional specific model to use
            
        Returns:
            BaseAIService implementation (Claude, OpenAI, or Mock)
            
        Example:
            # Use configured provider and model for chapter generation
            service = AIServiceFactory.get_service(UseCase.CHAPTER_GENERATION)
            
            # Force use of mock provider for testing
            service = AIServiceFactory.get_service(
                UseCase.CHAPTER_GENERATION, 
                provider_override="mock"
            )
            
            # Use specific model
            service = AIServiceFactory.get_service(
                UseCase.CHAPTER_GENERATION,
                model_override="gpt-4-turbo-preview"
            )
        """
        # Determine which model to use
        if model_override:
            model = model_override
        else:
            model = settings.get_model_for_use_case(use_case)

        # Determine which provider to use
        if provider_override:
            provider = provider_override.lower()
        else:
            provider = settings.get_provider_for_model(model)

        # Create cache key
        cache_key = f"{provider}:{model}"

        print(f"[FACTORY] get_service called - use_case={use_case}, provider={provider}, model={model}, cache_key={cache_key}")

        # Return cached instance if available
        if cache_key in cls._instances:
            print(f"[FACTORY] Returning CACHED {provider} service")
            return cls._instances[cache_key]

        # Create new service instance
        print(f"[FACTORY] Creating NEW {provider} service instance")
        if provider == "mock":
            service = MockAIService()
        elif provider == "claude":
            service = ClaudeAIService(model=model)
        elif provider == "openai":
            service = OpenAIService(model=model)
        elif provider == "gemini":
            service = GeminiAIService(model=model)
        else:
            raise ValueError(f"Unknown AI provider: {provider}")

        # Cache the instance
        cls._instances[cache_key] = service

        print(f"[FACTORY] Returning {provider} service with model {model}")
        return service
    
    @classmethod
    def get_chapter_service(cls, provider_override: Optional[str] = None) -> BaseAIService:
        """Convenience method for chapter generation."""
        return cls.get_service(UseCase.CHAPTER_GENERATION, provider_override)
    
    @classmethod
    def get_question_service(cls, provider_override: Optional[str] = None) -> BaseAIService:
        """Convenience method for question generation."""
        return cls.get_service(UseCase.QUESTION_GENERATION, provider_override)
    
    @classmethod
    def get_feedback_service(cls, provider_override: Optional[str] = None) -> BaseAIService:
        """Convenience method for student feedback."""
        return cls.get_service(UseCase.STUDENT_FEEDBACK, provider_override)
    
    @classmethod
    def get_answer_checking_service(cls, provider_override: Optional[str] = None) -> BaseAIService:
        """Convenience method for answer checking."""
        return cls.get_service(UseCase.ANSWER_CHECKING, provider_override)
    
    @classmethod
    def get_rag_service(cls, provider_override: Optional[str] = None) -> BaseAIService:
        """Convenience method for RAG queries."""
        return cls.get_service(UseCase.RAG_QUERY, provider_override)
    
    @classmethod
    def clear_cache(cls):
        """Clear cached service instances."""
        cls._instances.clear()
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available AI providers."""
        providers = ["mock"]  # Mock is always available

        if settings.anthropic_api_key:
            providers.append("claude")

        if settings.openai_api_key:
            providers.append("openai")

        if settings.google_api_key:
            providers.append("gemini")

        return providers
    
    @classmethod
    def get_provider_info(cls) -> dict:
        """
        Get information about configured providers and models.
        
        Returns:
            Dictionary with provider and model configuration
        """
        return {
            "default_provider": settings.default_ai_provider,
            "available_providers": cls.get_available_providers(),
            "models": {
                "chapter_generation": settings.model_chapter_generation,
                "question_generation": settings.model_question_generation,
                "student_feedback": settings.model_student_feedback,
                "answer_checking": settings.model_answer_checking,
                "rag_query": settings.model_rag_query
            },
            "ab_testing_enabled": settings.enable_ab_testing
        }
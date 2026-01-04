"""
Base AI Service Interface
All AI providers (Claude, OpenAI, Mock) implement this interface.
This ensures consistent input/output regardless of provider.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.course import Chapter, CourseConfig
from app.models.question import QuestionGenerationConfig, ChapterQuestions
from app.models.document_analysis import DocumentOutline, ConfirmedSection
from app.models.token_usage import TokenUsageRecord, OperationType
from app.db import token_repository


class BaseAIService(ABC):
    """
    Abstract base class for AI services.
    All AI providers must implement these methods with the same signature.
    """

    async def log_token_usage(
        self,
        operation: OperationType,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        course_id: Optional[str] = None
    ) -> None:
        """
        Log token usage to the database.

        Args:
            operation: Type of AI operation
            model: Model name used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            user_id: User who performed the operation (optional)
            context: Topic name or filenames (optional)
            course_id: Associated course ID (optional)
        """
        print(f"[TOKEN LOG] log_token_usage called - user_id={user_id} (type={type(user_id).__name__}), operation={operation}")

        if user_id is None:
            # Skip logging if no user_id provided
            print(f"[TOKEN LOG] Skipping - no user_id for {operation}")
            return

        print(f"[TOKEN LOG] Logging {operation} for user {user_id}: {input_tokens}+{output_tokens} tokens")

        record = TokenUsageRecord(
            user_id=user_id,
            operation=operation,
            provider=self.get_provider_name(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            context=context,
            course_id=course_id
        )
        try:
            result = await token_repository.save_token_usage(record)
            print(f"[TOKEN LOG] Saved with ID: {result}")
        except Exception as e:
            print(f"[TOKEN LOG] ERROR saving token usage: {e}")

    @abstractmethod
    async def generate_chapters(
        self,
        topic: str,
        config: CourseConfig,
        content: str = "",
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[Chapter]:
        """
        Generate chapters for a given topic using the provided configuration.

        Args:
            topic: The subject/topic for the course
            config: CourseConfig with recommended_chapters, difficulty, chapter_depth, time_per_chapter
            content: Optional document content to analyze
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            List of Chapter objects
        """
        pass
    
    @abstractmethod
    async def generate_questions(
        self,
        chapter: Chapter,
        num_mcq: int = 5,
        num_true_false: int = 3
    ) -> Dict[str, Any]:
        """
        Generate quiz questions for a chapter (legacy method).

        Args:
            chapter: The chapter object
            num_mcq: Number of multiple choice questions
            num_true_false: Number of true/false questions

        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays
        """
        pass

    async def generate_questions_from_config(
        self,
        config: QuestionGenerationConfig,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate quiz questions using a full configuration object.

        This method provides more control over question generation with
        audience targeting, key concepts, and detailed configuration.

        Args:
            config: QuestionGenerationConfig with all generation parameters
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays

        Note:
            Default implementation calls generate_questions() for backward compatibility.
            Providers can override this for enhanced generation.
        """
        # Default: create a minimal Chapter and delegate to generate_questions
        chapter = Chapter(
            number=config.chapter_number,
            title=config.chapter_title,
            summary=f"Chapter on {config.topic}",
            key_concepts=config.key_concepts,
            difficulty=config.difficulty
        )
        return await self.generate_questions(
            chapter,
            num_mcq=config.recommended_mcq_count,
            num_true_false=config.recommended_tf_count
        )
    
    @abstractmethod
    async def generate_feedback(
        self,
        user_progress: Dict[str, Any],
        weak_areas: List[str],
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate personalized student feedback.

        Args:
            user_progress: User's progress data
            weak_areas: Areas where student needs improvement
            user_id: User ID for token usage logging
            context: Context info for token logging

        Returns:
            Feedback message as string
        """
        pass

    @abstractmethod
    async def check_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if an answer is correct and provide explanation.

        Args:
            question: The question text
            user_answer: User's answer
            correct_answer: The correct answer
            user_id: User ID for token usage logging
            context: Context info for token logging

        Returns:
            Dictionary with 'is_correct', 'explanation', 'score'
        """
        pass

    @abstractmethod
    async def answer_question(
        self,
        question: str,
        rag_context: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Answer a student's question using RAG context.

        Args:
            question: Student's question
            rag_context: Relevant context from the material
            user_id: User ID for token usage logging
            context: Context info for token logging

        Returns:
            Answer as string
        """
        pass

    @abstractmethod
    async def analyze_document_structure(
        self,
        content: str,
        max_sections: int = 15,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> DocumentOutline:
        """
        Analyze document content and detect natural sections/chapters.

        This is Phase 1 of the two-phase file-to-course flow.
        The detected structure is shown to the user for review before
        generating detailed chapters.

        Args:
            content: Full extracted document text
            max_sections: Maximum number of sections to detect
            user_id: User ID for token usage logging
            context: Context info (filenames) for token logging

        Returns:
            DocumentOutline with detected structure
        """
        pass

    @abstractmethod
    async def generate_chapters_from_outline(
        self,
        topic: str,
        content: str,
        confirmed_sections: List[ConfirmedSection],
        difficulty: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[Chapter]:
        """
        Generate detailed chapters based on user-confirmed outline.

        This is Phase 2 of the two-phase file-to-course flow.
        Uses the confirmed section structure to generate chapters with
        rich key_ideas for question generation.

        Args:
            topic: Course topic (document title or user-specified)
            content: Full extracted document text
            confirmed_sections: User-confirmed sections (may be edited)
            difficulty: Course difficulty level
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            List of Chapter objects with key_ideas populated
        """
        pass

    def get_provider_name(self) -> str:
        """
        Get the name of this AI provider.
        
        Returns:
            Provider name (e.g., "claude", "openai", "mock")
        """
        return self.__class__.__name__.replace("Service", "").lower()
"""
Base AI Service Interface
All AI providers (Claude, OpenAI, Mock) implement this interface.
This ensures consistent input/output regardless of provider.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.course import Chapter


class BaseAIService(ABC):
    """
    Abstract base class for AI services.
    All AI providers must implement these methods with the same signature.
    """
    
    @abstractmethod
    async def generate_chapters(self, topic: str, difficulty: str = "intermediate", content: str = "") -> List[Chapter]:
        """
        Generate chapters for a given topic.

        Args:
            topic: The subject/topic for the course
            difficulty: Difficulty level for all chapters (beginner/intermediate/advanced)
            content: Optional document content to analyze

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
        Generate quiz questions for a chapter.
        
        Args:
            chapter: The chapter object
            num_mcq: Number of multiple choice questions
            num_true_false: Number of true/false questions
            
        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays
        """
        pass
    
    @abstractmethod
    async def generate_feedback(
        self, 
        user_progress: Dict[str, Any],
        weak_areas: List[str]
    ) -> str:
        """
        Generate personalized student feedback.
        
        Args:
            user_progress: User's progress data
            weak_areas: Areas where student needs improvement
            
        Returns:
            Feedback message as string
        """
        pass
    
    @abstractmethod
    async def check_answer(
        self, 
        question: str, 
        user_answer: str, 
        correct_answer: str
    ) -> Dict[str, Any]:
        """
        Check if an answer is correct and provide explanation.
        
        Args:
            question: The question text
            user_answer: User's answer
            correct_answer: The correct answer
            
        Returns:
            Dictionary with 'is_correct', 'explanation', 'score'
        """
        pass
    
    @abstractmethod
    async def answer_question(
        self, 
        question: str, 
        context: str
    ) -> str:
        """
        Answer a student's question using RAG context.
        
        Args:
            question: Student's question
            context: Relevant context from the material
            
        Returns:
            Answer as string
        """
        pass
    
    def get_provider_name(self) -> str:
        """
        Get the name of this AI provider.
        
        Returns:
            Provider name (e.g., "claude", "openai", "mock")
        """
        return self.__class__.__name__.replace("Service", "").lower()
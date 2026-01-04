"""
Question Analyzer Service
Analyzes chapters to determine optimal question counts using AI.
Uses caching to avoid redundant AI calls for the same chapter.
"""
import json
import hashlib
from typing import Optional, Dict
from pydantic import BaseModel, Field
from anthropic import AsyncAnthropic
from app.models.course import Chapter
from app.config import settings, UseCase


class QuestionCountRecommendation(BaseModel):
    """Recommendation for number of questions per chapter."""
    mcq_count: int = Field(..., ge=5, le=40, description="Recommended MCQ questions")
    true_false_count: int = Field(..., ge=3, le=15, description="Recommended True/False questions")
    total_count: int = Field(..., description="Total questions recommended")
    reasoning: str = Field(..., description="Explanation for the recommendation")

    class Config:
        json_schema_extra = {
            "example": {
                "mcq_count": 12,
                "true_false_count": 6,
                "total_count": 18,
                "reasoning": "This chapter covers 5 key concepts with moderate complexity, requiring comprehensive coverage."
            }
        }


# Default question counts per difficulty level
DEFAULT_COUNTS: Dict[str, Dict[str, int]] = {
    "beginner": {"mcq": 8, "tf": 5},
    "intermediate": {"mcq": 12, "tf": 6},
    "advanced": {"mcq": 20, "tf": 8},
}


class QuestionAnalyzer:
    """
    Analyzes chapters to determine optimal question count using AI.
    Caches results to avoid redundant API calls.
    """

    def __init__(self):
        """Initialize the question analyzer with AI client and cache."""
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._cache: Dict[str, QuestionCountRecommendation] = {}

    def _generate_cache_key(self, chapter: Chapter, topic: str, difficulty: str) -> str:
        """
        Generate a cache key based on chapter content.

        Args:
            chapter: The chapter to analyze
            topic: Course topic
            difficulty: Course difficulty

        Returns:
            Hash string as cache key
        """
        cache_input = f"{topic}|{difficulty}|{chapter.number}|{chapter.title}|{chapter.summary}|{','.join(chapter.key_concepts)}"
        return hashlib.sha256(cache_input.encode()).hexdigest()[:16]

    def _get_defaults(self, difficulty: str) -> QuestionCountRecommendation:
        """
        Get default question counts for a difficulty level.

        Args:
            difficulty: Course difficulty (beginner, intermediate, advanced)

        Returns:
            Default QuestionCountRecommendation
        """
        counts = DEFAULT_COUNTS.get(difficulty, DEFAULT_COUNTS["intermediate"])
        mcq = counts["mcq"]
        tf = counts["tf"]
        return QuestionCountRecommendation(
            mcq_count=mcq,
            true_false_count=tf,
            total_count=mcq + tf,
            reasoning=f"Default recommendation for {difficulty}-level content."
        )

    async def analyze_chapter(
        self,
        chapter: Chapter,
        topic: str,
        difficulty: str
    ) -> QuestionCountRecommendation:
        """
        Analyze a chapter to determine optimal question counts.

        If the chapter has key_ideas, calculates based on 2-3 questions per idea
        for ~80% coverage. Otherwise uses AI analysis.

        Args:
            chapter: The chapter to analyze
            topic: Course topic
            difficulty: Course difficulty level

        Returns:
            QuestionCountRecommendation with mcq_count, true_false_count, and reasoning
        """
        # Check cache first
        cache_key = self._generate_cache_key(chapter, topic, difficulty)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # NEW: If chapter has key_ideas, calculate based on coverage requirements
        if hasattr(chapter, 'key_ideas') and chapter.key_ideas and len(chapter.key_ideas) > 0:
            num_ideas = len(chapter.key_ideas)
            # Target 2.5 questions per idea for ~80% coverage
            total_questions = int(num_ideas * 2.5)
            total_questions = max(8, min(55, total_questions))  # Clamp to reasonable range

            # Split: 70% MCQ, 30% True/False
            mcq_count = max(5, min(40, int(total_questions * 0.7)))
            tf_count = max(3, min(15, total_questions - mcq_count))

            recommendation = QuestionCountRecommendation(
                mcq_count=mcq_count,
                true_false_count=tf_count,
                total_count=mcq_count + tf_count,
                reasoning=f"Based on {num_ideas} key ideas: generating ~2.5 questions per idea for 80% knowledge coverage."
            )

            # Cache the result
            self._cache[cache_key] = recommendation
            return recommendation

        # Fallback to AI analysis for chapters without key_ideas
        key_concepts_str = ", ".join(chapter.key_concepts) if chapter.key_concepts else "Not specified"

        prompt = f"""Given this chapter from a {difficulty} course on {topic}:

Chapter: {chapter.title}
Summary: {chapter.summary}
Key Concepts: {key_concepts_str}
Estimated Time: {chapter.estimated_time_minutes} minutes

How many questions are needed to comprehensively test this chapter?

Consider:
- Each key concept needs at least 1-2 questions
- Mix of easy/medium/hard questions for balanced assessment
- {difficulty} level appropriate depth
- Professional/certification topics (AWS, PMP, etc.) need more questions
- Simple introductory topics need fewer questions
- More concepts = more questions needed
- Chapter complexity and depth

Return ONLY valid JSON:
{{
  "mcq_count": number (minimum 5, maximum 40),
  "true_false_count": number (minimum 3, maximum 15),
  "reasoning": "brief explanation of your recommendation"
}}"""

        try:
            response = await self.client.messages.create(
                model=settings.model_question_count_analysis,
                max_tokens=settings.max_tokens_question_count,
                temperature=0.3,  # Low temperature for consistent analysis
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(json_text)

            # Validate and clamp values to acceptable ranges
            mcq_count = max(5, min(40, int(data.get("mcq_count", 10))))
            tf_count = max(3, min(15, int(data.get("true_false_count", 5))))

            recommendation = QuestionCountRecommendation(
                mcq_count=mcq_count,
                true_false_count=tf_count,
                total_count=mcq_count + tf_count,
                reasoning=data.get("reasoning", "AI-based analysis of chapter content.")
            )

            # Cache the result
            self._cache[cache_key] = recommendation

            return recommendation

        except Exception as e:
            # If AI fails, return sensible defaults based on difficulty
            default = self._get_defaults(difficulty)
            default.reasoning = f"Default used due to analysis error: {str(e)[:50]}"
            return default

    def get_cached_count(self) -> int:
        """Get the number of cached recommendations."""
        return len(self._cache)

    def clear_cache(self) -> None:
        """Clear the recommendation cache."""
        self._cache.clear()


# Singleton instance for easy access
_analyzer_instance: Optional[QuestionAnalyzer] = None


def get_question_analyzer() -> QuestionAnalyzer:
    """Get or create the QuestionAnalyzer singleton instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = QuestionAnalyzer()
    return _analyzer_instance

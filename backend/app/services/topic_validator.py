"""
Topic Validator Service
Validates topics before course generation to ensure they are appropriate scope.
Uses quick pattern matching and AI-based validation.
"""
import json
import re
from typing import Optional
from app.models.validation import TopicValidationResult, TopicComplexity, TopicCategory
from app.config import settings
from app.utils.llm_logger import llm_logger


# Broad single-word topics that should be rejected
BROAD_TOPICS = {
    "physics", "math", "mathematics", "business", "science", "engineering",
    "medicine", "law", "history", "chemistry", "biology", "economics",
    "psychology", "sociology", "philosophy", "art", "music", "literature",
    "technology", "computer", "programming", "marketing", "finance",
    "management", "education", "health", "politics", "geography"
}

# Specific single-word topics that are acceptable (known courses)
ALLOWED_SINGLE_WORDS = {
    "calculus", "algebra", "geometry", "trigonometry", "statistics",
    "photoshop", "excel", "powerpoint", "docker", "kubernetes", "git",
    "javascript", "python", "java", "rust", "golang", "typescript",
    "react", "angular", "vue", "django", "flask", "fastapi",
    "sql", "mongodb", "redis", "elasticsearch", "graphql"
}

# Vague terms that indicate unclear topics
VAGUE_TERMS = {
    "stuff", "things", "about", "everything", "misc", "miscellaneous",
    "random", "various", "general", "basic", "advanced", "intro",
    "something", "anything", "whatever", "etc", "other"
}


class TopicValidator:
    """
    Validates course topics using quick pattern checks and AI analysis.
    """

    def __init__(self):
        """Initialize the topic validator."""
        self.model = settings.model_topic_validation
        self.provider = settings.get_provider_for_model(self.model)
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate AI client based on provider."""
        if self.provider == "claude":
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            # Mock provider - no client needed
            self.client = None

    def _normalize_topic(self, topic: str) -> str:
        """
        Normalize a topic string for comparison.

        Args:
            topic: Raw topic string

        Returns:
            Normalized topic (lowercase, trimmed, single spaces)
        """
        # Lowercase and strip
        normalized = topic.lower().strip()
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _count_words(self, topic: str) -> int:
        """Count words in a topic string."""
        return len(topic.split())

    def quick_validate(self, topic: str) -> Optional[TopicValidationResult]:
        """
        Perform quick validation using pattern matching.
        Returns a rejection result if the topic fails, None if it passes.

        Args:
            topic: The topic to validate

        Returns:
            TopicValidationResult if rejected, None if passes quick validation
        """
        normalized = self._normalize_topic(topic)
        word_count = self._count_words(normalized)
        words = set(normalized.split())

        # Check for vague terms
        vague_found = words & VAGUE_TERMS
        if vague_found:
            return TopicValidationResult(
                status="rejected",
                topic=topic,
                normalized_topic=normalized,
                reason="unclear",
                message=f"The topic contains vague terms: {', '.join(vague_found)}. Please be more specific.",
                suggestions=[
                    f"Try specifying what aspect of '{topic}' you want to learn",
                    "Add context like 'for beginners' or 'practical applications'",
                    "Focus on a specific subtopic or skill"
                ]
            )

        # Check single-word topics
        if word_count == 1:
            # Allow specific known courses
            if normalized in ALLOWED_SINGLE_WORDS:
                return None  # Passes quick validation

            # Reject broad single-word topics
            if normalized in BROAD_TOPICS:
                return TopicValidationResult(
                    status="rejected",
                    topic=topic,
                    normalized_topic=normalized,
                    reason="too_broad",
                    message=f"'{topic}' is too broad for a single course. Please narrow down to a specific area.",
                    suggestions=self._get_narrowing_suggestions(normalized)
                )

            # Reject other single words (likely too vague)
            return TopicValidationResult(
                status="needs_clarification",
                topic=topic,
                normalized_topic=normalized,
                reason="unclear",
                message=f"'{topic}' is a single word. Could you be more specific about what you want to learn?",
                suggestions=[
                    f"'{topic}' fundamentals",
                    f"Introduction to {topic}",
                    f"Practical {topic} skills"
                ]
            )

        # Check for topics that are too short (less than 2 meaningful words)
        # Filter out common filler words
        filler_words = {"the", "a", "an", "to", "for", "of", "in", "on", "and", "or", "with"}
        meaningful_words = [w for w in normalized.split() if w not in filler_words]

        if len(meaningful_words) < 2:
            return TopicValidationResult(
                status="needs_clarification",
                topic=topic,
                normalized_topic=normalized,
                reason="unclear",
                message="The topic needs more specificity. Please add more detail.",
                suggestions=[
                    "Add the specific area or application you're interested in",
                    "Specify the level (beginner, intermediate, advanced)",
                    "Mention the context (for work, for certification, etc.)"
                ]
            )

        # Passes quick validation
        return None

    def _get_narrowing_suggestions(self, broad_topic: str) -> list:
        """Get suggestions for narrowing down a broad topic."""
        suggestions_map = {
            "physics": [
                "Classical Mechanics for Engineers",
                "Introduction to Quantum Physics",
                "Thermodynamics Fundamentals"
            ],
            "math": [
                "Linear Algebra for Data Science",
                "Calculus for Machine Learning",
                "Statistics for Business Analytics"
            ],
            "mathematics": [
                "Discrete Mathematics for Computer Science",
                "Mathematical Logic",
                "Probability Theory"
            ],
            "business": [
                "Business Strategy Fundamentals",
                "Financial Accounting Basics",
                "Marketing for Startups"
            ],
            "science": [
                "Scientific Method and Research Design",
                "Data Science Fundamentals",
                "Environmental Science Basics"
            ],
            "engineering": [
                "Software Engineering Principles",
                "Civil Engineering Fundamentals",
                "Systems Engineering Basics"
            ],
            "programming": [
                "Python Programming for Beginners",
                "Web Development with JavaScript",
                "Object-Oriented Programming Concepts"
            ],
            "computer": [
                "Computer Science Fundamentals",
                "Computer Networking Basics",
                "Operating Systems Concepts"
            ],
            "history": [
                "World War II: Causes and Consequences",
                "History of the Roman Empire",
                "American Civil Rights Movement"
            ],
            "medicine": [
                "Human Anatomy Basics",
                "Pharmacology Fundamentals",
                "Medical Terminology"
            ]
        }

        return suggestions_map.get(broad_topic, [
            f"Introduction to {broad_topic.title()}",
            f"{broad_topic.title()} for Beginners",
            f"Practical {broad_topic.title()} Skills"
        ])

    async def ai_validate(self, topic: str) -> TopicValidationResult:
        """
        Use AI to validate and analyze the topic.

        Args:
            topic: The topic to validate

        Returns:
            TopicValidationResult with full analysis
        """
        normalized = self._normalize_topic(topic)

        prompt = f"""Analyze this educational topic for a course generation system.

Topic: "{topic}"

IMPORTANT: If this topic is a recognized certification, professional credential, or standardized exam (e.g., CAPM, PMP, AWS, CISSP, CPA, etc.):
- Treat it as VALID - these are well-defined learning paths
- Use your knowledge of the official syllabus/exam domains
- Base the complexity and chapter estimates on the actual certification curriculum
- The estimated_chapters should align with the certification's official domains/modules

Evaluate and respond with ONLY valid JSON (no additional text):

{{
  "is_valid": true/false,
  "is_certification": true/false,
  "certification_body": "Name of certifying organization if applicable, null otherwise",
  "category": "official_certification" or "college_course" or "high_school" or "middle_school" or "elementary_school" or "general_knowledge",
  "reason": null or "too_broad" or "too_narrow" or "unclear" or "inappropriate",
  "message": "Brief explanation of your assessment",
  "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
  "complexity": {{
    "score": 1-10,
    "level": "basic" or "intermediate" or "advanced" or "expert",
    "estimated_chapters": number,
    "estimated_hours": number,
    "reasoning": "Why this complexity rating"
  }}
}}

Category Guidelines:
- "official_certification": Professional certifications (AWS, PMP, CISSP, CPA, CAPM, CompTIA, etc.)
- "college_course": University/college level academic subjects (calculus, organic chemistry, etc.)
- "high_school": High school curriculum topics (grades 9-12, AP courses, SAT prep)
- "middle_school": Middle school curriculum topics (grades 6-8)
- "elementary_school": Elementary school topics (grades 1-5, basic math, reading)
- "general_knowledge": Hobbies, skills, general interest topics (photography, cooking, guitar)

Validation Guidelines:
- A valid topic can be covered in 4-20 chapters (a single focused course)
- Certifications are ALWAYS valid - they have official curricula
- "too_broad" = would need multiple courses (e.g., "Computer Science")
- "too_narrow" = not enough content for a course (e.g., "How to print Hello World")
- "unclear" = ambiguous or vague topic
- "inappropriate" = offensive or not educational
- Complexity score: 1=trivial, 5=moderate, 10=extremely complex
- For certifications, base estimated_chapters on official exam domains"""

        try:
            start_time = llm_logger.log_request(self.model, prompt, "Topic Validation")

            # Call appropriate provider
            if self.provider == "claude":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=settings.max_tokens_validation,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            elif self.provider == "gemini":
                # Gemini uses sync API, run in executor
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.3,
                            "max_output_tokens": settings.max_tokens_validation
                        }
                    )
                )
                response_text = response.text
            elif self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=settings.max_tokens_validation,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.choices[0].message.content
            else:
                # Mock provider - return a default accepted response
                return TopicValidationResult(
                    status="accepted",
                    topic=topic,
                    normalized_topic=normalized,
                    message="Topic validated (mock provider)",
                    complexity=TopicComplexity(
                        score=5,
                        level="intermediate",
                        estimated_chapters=6,
                        estimated_hours=10.0,
                        reasoning="Mock validation"
                    ),
                    category=TopicCategory.GENERAL_KNOWLEDGE
                )

            llm_logger.log_response(start_time, "Topic Validation")

            # Extract JSON from response
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(json_text)

            # Build complexity object if provided
            complexity = None
            if data.get("complexity"):
                complexity = TopicComplexity(
                    score=data["complexity"]["score"],
                    level=data["complexity"]["level"],
                    estimated_chapters=data["complexity"]["estimated_chapters"],
                    estimated_hours=data["complexity"]["estimated_hours"],
                    reasoning=data["complexity"]["reasoning"]
                )

            # Determine status
            if data["is_valid"]:
                status = "accepted"
            elif data.get("reason") == "unclear":
                status = "needs_clarification"
            else:
                status = "rejected"

            # Parse category
            category = None
            if data.get("category"):
                try:
                    category = TopicCategory(data["category"])
                except ValueError:
                    category = TopicCategory.GENERAL_KNOWLEDGE

            return TopicValidationResult(
                status=status,
                topic=topic,
                normalized_topic=normalized,
                reason=data.get("reason"),
                message=data["message"],
                suggestions=data.get("suggestions", []),
                complexity=complexity,
                is_certification=data.get("is_certification", False),
                certification_body=data.get("certification_body"),
                category=category
            )

        except Exception as e:
            # If AI validation fails, return a needs_clarification result
            return TopicValidationResult(
                status="needs_clarification",
                topic=topic,
                normalized_topic=normalized,
                reason="unclear",
                message=f"Could not validate topic. Please try rephrasing: {str(e)}",
                suggestions=[
                    "Try being more specific about the subject area",
                    "Add context like the target audience or skill level",
                    "Mention the practical application or goal"
                ]
            )

    async def validate(self, topic: str) -> TopicValidationResult:
        """
        Full validation: quick check followed by AI validation if needed.

        Args:
            topic: The topic to validate

        Returns:
            TopicValidationResult with full analysis
        """
        # First, run quick validation
        quick_result = self.quick_validate(topic)
        if quick_result is not None:
            # Quick validation rejected or needs clarification
            return quick_result

        # Quick validation passed, run AI validation for deeper analysis
        return await self.ai_validate(topic)


# Singleton instance for easy access
_validator_instance: Optional[TopicValidator] = None


def get_topic_validator() -> TopicValidator:
    """Get or create the TopicValidator singleton instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = TopicValidator()
    return _validator_instance

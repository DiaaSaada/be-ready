"""
Question Generator Service
Orchestrates AI-based question generation for course chapters.
Handles prompt building, response parsing, validation, and retry logic.
"""
import json
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging for failed responses
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logger = logging.getLogger(__name__)
from app.models.course import Chapter
from app.models.question import (
    QuestionGenerationConfig,
    ChapterQuestions,
    MCQQuestion,
    TrueFalseQuestion,
    QuestionDifficulty,
)
from app.services.question_analyzer import QuestionAnalyzer, get_question_analyzer
from app.services.ai_service_factory import AIServiceFactory
from app.config import settings, UseCase
from app.db import crud


# Audience descriptions based on difficulty
AUDIENCE_DESCRIPTIONS: Dict[str, str] = {
    "beginner": "teenagers and beginners; use simple language, short questions, avoid jargon",
    "intermediate": "college students and working professionals; technical terms allowed, medium-length questions",
    "advanced": "experienced professionals and experts; industry jargon acceptable, complex scenario-based questions allowed",
}


class QuestionGenerator:
    """
    Generates quiz questions for course chapters using AI.

    Handles the full question generation pipeline:
    1. Derives audience from difficulty
    2. Builds optimized prompts
    3. Calls AI service
    4. Parses and validates response
    5. Creates strongly-typed question objects
    """

    def __init__(
        self,
        question_analyzer: Optional[QuestionAnalyzer] = None
    ):
        """
        Initialize the question generator.

        Args:
            question_analyzer: Optional analyzer for determining question counts.
                             Uses singleton if not provided.
        """
        self.question_analyzer = question_analyzer or get_question_analyzer()

    def _get_ai_service(self):
        """Get the AI service for question generation based on config."""
        return AIServiceFactory.get_service(UseCase.QUESTION_GENERATION)

    def _derive_audience(self, difficulty: str) -> str:
        """
        Derive target audience description from difficulty level.

        Args:
            difficulty: Course difficulty (beginner, intermediate, advanced)

        Returns:
            Audience description for prompt
        """
        return AUDIENCE_DESCRIPTIONS.get(
            difficulty,
            AUDIENCE_DESCRIPTIONS["intermediate"]
        )

    def _build_prompt(self, config: QuestionGenerationConfig) -> str:
        """
        Build the AI prompt for question generation.

        Args:
            config: Question generation configuration

        Returns:
            Formatted prompt string
        """
        key_concepts_str = ", ".join(config.key_concepts) if config.key_concepts else "General chapter concepts"

        # Determine question length guidance based on difficulty
        if config.difficulty == "beginner":
            length_guidance = "Keep questions SHORT (1-2 lines). Use simple vocabulary."
        elif config.difficulty == "advanced":
            length_guidance = "Scenario-based questions can be LONGER (3-8 lines). Use precise technical language."
        else:
            length_guidance = "Questions should be MODERATE length (2-4 lines). Balance clarity with depth."

        # Build key_ideas section if available (for 80% coverage)
        key_ideas_section = ""
        if hasattr(config, 'key_ideas') and config.key_ideas and len(config.key_ideas) > 0:
            ideas_list = "\n".join([f"  - {idea}" for idea in config.key_ideas])
            key_ideas_section = f"""
KEY IDEAS TO COVER (REQUIRED - generate at least 1 question per idea):
{ideas_list}

COVERAGE REQUIREMENT: Ensure at least 80% of the key ideas above are tested.
Each key idea should have 2-3 questions testing different aspects."""

        prompt = f"""You are an expert exam creator designing questions for {config.audience}.

Create questions for this chapter from a {config.difficulty} course on {config.topic}.

Chapter {config.chapter_number}: {config.chapter_title}
Key Concepts: {key_concepts_str}
{key_ideas_section}

Generate EXACTLY:
- {config.recommended_mcq_count} Multiple Choice Questions
- {config.recommended_tf_count} True/False Questions

RULES:
1. Language must be appropriate for {config.audience}
2. {length_guidance}
3. Cover ALL key concepts (at least 1 question per concept)
4. If key ideas are provided, ensure each key idea has at least 1 question
5. Mix difficulties: ~30% easy, ~50% medium, ~20% hard
6. MCQ options: exactly 4 options (A, B, C, D), one clearly correct, plausible distractors
7. NO trick questions or deliberately confusing wording
8. NO "All of the above" or "None of the above" options
9. Each question MUST have a clear explanation for the correct answer
10. True/False statements must be definitively true or false, not ambiguous

CRITICAL JSON FORMATTING:
- Return ONLY valid JSON, no markdown code blocks, no extra text
- Use double quotes for ALL strings (never single quotes)
- Escape quotes inside strings with backslash: \\"
- NO trailing commas after last item in arrays or objects
- difficulty must be exactly: "easy", "medium", or "hard"
- correct_answer for MCQ must be exactly: "A", "B", "C", or "D"
- correct_answer for true_false must be: true or false (no quotes)

Return this exact JSON structure:
{{
  "mcq": [
    {{
      "question_text": "Clear question text here?",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "correct_answer": "A",
      "explanation": "Explanation of why A is correct...",
      "difficulty": "easy"
    }}
  ],
  "true_false": [
    {{
      "question_text": "A clear statement that is definitively true or false.",
      "correct_answer": true,
      "explanation": "Explanation of why this is true/false...",
      "difficulty": "medium"
    }}
  ]
}}"""

        return prompt

    def _log_failed_response(self, response_text: str, error: Exception, attempt: int) -> str:
        """Log failed AI response to a file for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"failed_response_{timestamp}_attempt{attempt}.txt"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Failed JSON Parse ===\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Attempt: {attempt}\n")
            f.write(f"Error: {str(error)}\n")
            f.write(f"Response length: {len(response_text)} chars\n")
            f.write(f"\n=== Raw Response ===\n")
            f.write(response_text)
            f.write(f"\n\n=== End ===\n")

        logger.error(f"Failed response logged to: {log_file}")
        return str(log_file)

    def _parse_response(self, response_text: str, attempt: int = 1) -> Dict[str, Any]:
        """
        Parse AI response to extract JSON.

        Args:
            response_text: Raw response from AI
            attempt: Current attempt number for logging

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If parsing fails
        """
        import re

        # Clean up response - extract JSON from potential markdown
        json_text = response_text.strip()

        # Remove markdown code blocks
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        # Try to find JSON object if there's extra text
        if not json_text.startswith("{"):
            # Find the first { and last }
            start = json_text.find("{")
            end = json_text.rfind("}") + 1
            if start != -1 and end > start:
                json_text = json_text[start:end]

        # Fix common JSON issues from LLMs
        # Remove trailing commas before } or ]
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

        # Remove control characters except newlines and tabs
        json_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', json_text)

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Log the failed response
            log_file = self._log_failed_response(response_text, e, attempt)

            # Try a more aggressive cleanup
            # Remove any text after the last valid }
            depth = 0
            last_valid_pos = 0
            in_string = False
            escape_next = False

            for i, char in enumerate(json_text):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        last_valid_pos = i + 1
                        break

            if last_valid_pos > 0:
                json_text = json_text[:last_valid_pos]
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass  # Fall through to raise original error

            raise json.JSONDecodeError(
                f"{e.msg} (logged to {log_file})",
                e.doc,
                e.pos
            )

    def _map_difficulty(self, difficulty_str: str) -> QuestionDifficulty:
        """Map string difficulty to enum."""
        mapping = {
            "easy": QuestionDifficulty.EASY,
            "medium": QuestionDifficulty.MEDIUM,
            "hard": QuestionDifficulty.HARD,
        }
        return mapping.get(difficulty_str.lower(), QuestionDifficulty.MEDIUM)

    def _create_mcq_questions(self, mcq_data: list) -> list[MCQQuestion]:
        """
        Create MCQQuestion objects from parsed data.

        Args:
            mcq_data: List of MCQ dictionaries from AI

        Returns:
            List of MCQQuestion objects
        """
        questions = []
        for item in mcq_data:
            try:
                question = MCQQuestion(
                    id=str(uuid.uuid4()),
                    difficulty=self._map_difficulty(item.get("difficulty", "medium")),
                    question_text=item["question_text"],
                    options=item["options"],
                    correct_answer=item["correct_answer"],
                    explanation=item["explanation"],
                    points=1
                )
                questions.append(question)
            except Exception:
                # Skip malformed questions
                continue
        return questions

    def _create_tf_questions(self, tf_data: list) -> list[TrueFalseQuestion]:
        """
        Create TrueFalseQuestion objects from parsed data.

        Args:
            tf_data: List of T/F dictionaries from AI

        Returns:
            List of TrueFalseQuestion objects
        """
        questions = []
        for item in tf_data:
            try:
                question = TrueFalseQuestion(
                    id=str(uuid.uuid4()),
                    difficulty=self._map_difficulty(item.get("difficulty", "medium")),
                    question_text=item["question_text"],
                    correct_answer=bool(item["correct_answer"]),
                    explanation=item["explanation"],
                    points=1
                )
                questions.append(question)
            except Exception:
                # Skip malformed questions
                continue
        return questions

    def _validate_questions(
        self,
        mcq_questions: list[MCQQuestion],
        tf_questions: list[TrueFalseQuestion],
        config: QuestionGenerationConfig
    ) -> tuple[bool, str]:
        """
        Validate generated questions meet requirements.

        Args:
            mcq_questions: Generated MCQ questions
            tf_questions: Generated T/F questions
            config: Original configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        mcq_count = len(mcq_questions)
        tf_count = len(tf_questions)

        # Allow some tolerance (80% of requested)
        min_mcq = max(1, int(config.recommended_mcq_count * 0.8))
        min_tf = max(1, int(config.recommended_tf_count * 0.8))

        if mcq_count < min_mcq:
            return False, f"Not enough MCQ questions: got {mcq_count}, need at least {min_mcq}"

        if tf_count < min_tf:
            return False, f"Not enough T/F questions: got {tf_count}, need at least {min_tf}"

        return True, ""

    async def generate_questions(
        self,
        config: QuestionGenerationConfig,
        max_retries: int = 1,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> ChapterQuestions:
        """
        Generate questions for a chapter using AI.

        Args:
            config: Question generation configuration
            max_retries: Number of retries on failure (default 1)

        Returns:
            ChapterQuestions object with generated questions

        Raises:
            Exception: If generation fails after all retries
        """
        # Derive audience if generic
        if not config.audience or config.audience == "general learners":
            config = QuestionGenerationConfig(
                topic=config.topic,
                difficulty=config.difficulty,
                audience=self._derive_audience(config.difficulty),
                chapter_number=config.chapter_number,
                chapter_title=config.chapter_title,
                key_concepts=config.key_concepts,
                recommended_mcq_count=config.recommended_mcq_count,
                recommended_tf_count=config.recommended_tf_count
            )

        last_error = None
        ai_service = self._get_ai_service()

        for attempt in range(max_retries + 1):
            try:
                # Use the AI service to generate questions
                chapter_questions = await ai_service.generate_questions_from_config(
                    config,
                    user_id=user_id,
                    context=context or config.topic
                )

                # Validate
                is_valid, error_msg = self._validate_questions(
                    chapter_questions.mcq_questions,
                    chapter_questions.true_false_questions,
                    config
                )

                if not is_valid and attempt < max_retries:
                    last_error = error_msg
                    continue

                return chapter_questions

            except json.JSONDecodeError as e:
                last_error = f"JSON parsing failed: {str(e)}"
                if attempt < max_retries:
                    continue
                raise Exception(f"Failed to parse AI response after {max_retries + 1} attempts: {last_error}")

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    continue
                raise

        # Should not reach here, but just in case
        raise Exception(f"Question generation failed: {last_error}")

    async def generate_questions_for_chapter(
        self,
        chapter: Chapter,
        topic: str,
        difficulty: str,
        override_mcq_count: Optional[int] = None,
        override_tf_count: Optional[int] = None
    ) -> ChapterQuestions:
        """
        Convenience method to generate questions directly from a Chapter object.

        Args:
            chapter: The chapter to generate questions for
            topic: Course topic
            difficulty: Course difficulty
            override_mcq_count: Optional override for MCQ count
            override_tf_count: Optional override for T/F count

        Returns:
            ChapterQuestions object
        """
        # Get recommended counts from analyzer if not overridden
        if override_mcq_count is None or override_tf_count is None:
            recommendation = await self.question_analyzer.analyze_chapter(
                chapter, topic, difficulty
            )
            mcq_count = override_mcq_count or recommendation.mcq_count
            tf_count = override_tf_count or recommendation.true_false_count
        else:
            mcq_count = override_mcq_count
            tf_count = override_tf_count

        # Build config
        config = QuestionGenerationConfig(
            topic=topic,
            difficulty=difficulty,
            audience=self._derive_audience(difficulty),
            chapter_number=chapter.number,
            chapter_title=chapter.title,
            key_concepts=chapter.key_concepts,
            recommended_mcq_count=mcq_count,
            recommended_tf_count=tf_count
        )

        return await self.generate_questions(config)

    def _build_concept_prompt(
        self,
        config: QuestionGenerationConfig,
        concept: str,
        mcq_count: int,
        tf_count: int
    ) -> str:
        """
        Build the AI prompt for generating questions about a single concept.

        Args:
            config: Question generation configuration
            concept: The specific key concept to generate questions for
            mcq_count: Number of MCQ questions to generate
            tf_count: Number of True/False questions to generate

        Returns:
            Formatted prompt string
        """
        # Determine question length guidance based on difficulty
        if config.difficulty == "beginner":
            length_guidance = "Keep questions SHORT (1-2 lines). Use simple vocabulary."
        elif config.difficulty == "advanced":
            length_guidance = "Scenario-based questions can be LONGER (3-8 lines). Use precise technical language."
        else:
            length_guidance = "Questions should be MODERATE length (2-4 lines). Balance clarity with depth."

        prompt = f"""You are an expert exam creator designing questions for {config.audience}.

Create questions about the concept "{concept}" from Chapter {config.chapter_number}: {config.chapter_title} of a {config.difficulty} course on {config.topic}.

Generate EXACTLY:
- {mcq_count} Multiple Choice Questions about "{concept}"
- {tf_count} True/False Questions about "{concept}"

RULES:
1. Language must be appropriate for {config.audience}
2. {length_guidance}
3. ALL questions must directly relate to "{concept}"
4. Mix difficulties: ~30% easy, ~50% medium, ~20% hard
5. MCQ options: exactly 4 options (A, B, C, D), one clearly correct, plausible distractors
6. NO trick questions or deliberately confusing wording
7. NO "All of the above" or "None of the above" options
8. Each question MUST have a clear explanation for the correct answer
9. True/False statements must be definitively true or false, not ambiguous

CRITICAL JSON FORMATTING:
- Return ONLY valid JSON, no markdown code blocks, no extra text
- Use double quotes for ALL strings (never single quotes)
- Escape quotes inside strings with backslash: \\"
- NO trailing commas after last item in arrays or objects
- difficulty must be exactly: "easy", "medium", or "hard"
- correct_answer for MCQ must be exactly: "A", "B", "C", or "D"
- correct_answer for true_false must be: true or false (no quotes)

Return this exact JSON structure:
{{
  "mcq": [
    {{
      "question_text": "Clear question text here?",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "correct_answer": "A",
      "explanation": "Explanation of why A is correct...",
      "difficulty": "easy"
    }}
  ],
  "true_false": [
    {{
      "question_text": "A clear statement that is definitively true or false.",
      "correct_answer": true,
      "explanation": "Explanation of why this is true/false...",
      "difficulty": "medium"
    }}
  ]
}}"""

        return prompt

    async def generate_questions_chunked(
        self,
        config: QuestionGenerationConfig,
        save_incrementally: bool = True,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> ChapterQuestions:
        """
        Generate questions per key_concept with incremental MongoDB saves.

        This method generates questions in smaller batches (one per concept)
        to avoid response truncation issues with large question sets.

        Args:
            config: Question generation configuration
            save_incrementally: Whether to save each batch to MongoDB

        Returns:
            ChapterQuestions object with all generated questions

        Raises:
            Exception: If generation fails for all concepts
        """
        # Derive audience if generic
        if not config.audience or config.audience == "general learners":
            config = QuestionGenerationConfig(
                topic=config.topic,
                difficulty=config.difficulty,
                audience=self._derive_audience(config.difficulty),
                chapter_number=config.chapter_number,
                chapter_title=config.chapter_title,
                key_concepts=config.key_concepts,
                recommended_mcq_count=config.recommended_mcq_count,
                recommended_tf_count=config.recommended_tf_count
            )

        # Calculate questions per concept
        num_concepts = len(config.key_concepts) if config.key_concepts else 1
        mcq_per_concept = max(2, config.recommended_mcq_count // num_concepts)
        tf_per_concept = max(1, config.recommended_tf_count // num_concepts)

        # Handle leftover questions for the last concept
        leftover_mcq = config.recommended_mcq_count - (mcq_per_concept * num_concepts)
        leftover_tf = config.recommended_tf_count - (tf_per_concept * num_concepts)

        all_mcq_questions: list[MCQQuestion] = []
        all_tf_questions: list[TrueFalseQuestion] = []
        failed_concepts: list[str] = []

        concepts = config.key_concepts if config.key_concepts else [config.topic]
        ai_service = self._get_ai_service()
        provider_name = ai_service.get_provider_name()

        for i, concept in enumerate(concepts):
            # Add leftover questions to the last concept
            is_last = (i == len(concepts) - 1)
            mcq_count = mcq_per_concept + (leftover_mcq if is_last else 0)
            tf_count = tf_per_concept + (leftover_tf if is_last else 0)

            logger.info(f"Generating questions for concept {i+1}/{len(concepts)}: {concept}")

            try:
                # Create a concept-specific config
                concept_config = QuestionGenerationConfig(
                    topic=config.topic,
                    difficulty=config.difficulty,
                    audience=config.audience,
                    chapter_number=config.chapter_number,
                    chapter_title=f"{config.chapter_title} - {concept}",
                    key_concepts=[concept],
                    recommended_mcq_count=mcq_count,
                    recommended_tf_count=tf_count
                )

                # Use AI service to generate questions
                chunk_result = await ai_service.generate_questions_from_config(
                    concept_config,
                    user_id=user_id,
                    context=context or config.topic
                )

                # Extract questions
                mcq_questions = chunk_result.mcq_questions
                tf_questions = chunk_result.true_false_questions

                # Add to accumulators
                all_mcq_questions.extend(mcq_questions)
                all_tf_questions.extend(tf_questions)

                # Save batch to MongoDB if enabled
                if save_incrementally:
                    await crud.save_question_batch(
                        course_topic=config.topic,
                        difficulty=config.difficulty,
                        chapter_number=config.chapter_number,
                        key_concept=concept,
                        mcq=[q.model_dump() for q in mcq_questions],
                        true_false=[q.model_dump() for q in tf_questions],
                        provider=provider_name
                    )

                logger.info(f"Generated {len(mcq_questions)} MCQ + {len(tf_questions)} T/F for '{concept}'")

            except Exception as e:
                logger.error(f"Failed to generate questions for concept '{concept}': {e}")
                failed_concepts.append(concept)
                continue

        # Log summary
        if failed_concepts:
            logger.warning(f"Failed concepts: {failed_concepts}")

        if not all_mcq_questions and not all_tf_questions:
            raise Exception(f"Failed to generate any questions. Failed concepts: {failed_concepts}")

        # Aggregate batches in MongoDB if we saved incrementally
        if save_incrementally:
            await crud.aggregate_question_batches(
                course_topic=config.topic,
                difficulty=config.difficulty,
                chapter_number=config.chapter_number,
                chapter_title=config.chapter_title
            )
            # Clean up batch documents
            await crud.delete_question_batches(
                course_topic=config.topic,
                difficulty=config.difficulty,
                chapter_number=config.chapter_number
            )

        # Build result
        return ChapterQuestions(
            chapter_number=config.chapter_number,
            chapter_title=config.chapter_title,
            mcq_questions=all_mcq_questions,
            true_false_questions=all_tf_questions
        )


# Singleton instance
_generator_instance: Optional[QuestionGenerator] = None


def get_question_generator() -> QuestionGenerator:
    """Get or create the QuestionGenerator singleton instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = QuestionGenerator()
    return _generator_instance

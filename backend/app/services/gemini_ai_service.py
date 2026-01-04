"""
Gemini AI Service
Implementation using Google's Gemini API.
Implements BaseAIService interface.
"""
from typing import List, Dict, Any, Optional
import json
import uuid
import google.generativeai as genai
from app.models.course import Chapter, CourseConfig
from app.models.document_analysis import DocumentOutline, DetectedSection, ConfirmedSection
from app.models.question import (
    QuestionGenerationConfig,
    ChapterQuestions,
    MCQQuestion,
    TrueFalseQuestion,
    QuestionDifficulty,
)
from app.models.token_usage import OperationType
from app.services.base_ai_service import BaseAIService
from app.config import settings
from app.utils.llm_logger import llm_logger


# Audience descriptions for question generation
AUDIENCE_DESCRIPTIONS: Dict[str, str] = {
    "beginner": "teenagers and beginners; use simple language, short questions, avoid jargon",
    "intermediate": "college students and working professionals; technical terms allowed, medium-length questions",
    "advanced": "experienced professionals and experts; industry jargon acceptable, complex scenario-based questions allowed",
}


class GeminiAIService(BaseAIService):
    """
    Gemini AI service for production use.
    Makes actual API calls to Google's Gemini models.
    """

    def __init__(self, model: str = None):
        """
        Initialize Gemini AI service.

        Args:
            model: Optional model override. If not provided, uses gemini-1.5-flash.
        """
        if not settings.google_api_key:
            raise ValueError("Google API key not configured. Set GOOGLE_API_KEY in .env")
        genai.configure(api_key=settings.google_api_key)
        self.default_model = model or "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.default_model)

    async def generate_chapters(
        self,
        topic: str,
        config: CourseConfig,
        content: str = "",
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[Chapter]:
        """
        Generate chapters using Gemini AI.

        Args:
            topic: The subject/topic for the course
            config: CourseConfig with chapter count, difficulty, depth, and time settings
            content: Optional document content to analyze
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            List of Chapter objects
        """
        # Extract config values
        num_chapters = config.recommended_chapters
        difficulty = config.difficulty
        depth = config.chapter_depth
        time_per_chapter = config.time_per_chapter_minutes

        # Depth descriptions
        depth_descriptions = {
            "overview": "surface-level concepts and key terminology",
            "detailed": "practical depth with explanations and examples",
            "comprehensive": "expert-level content with advanced concepts and case studies"
        }
        depth_desc = depth_descriptions.get(depth, depth_descriptions["detailed"])

        # Difficulty-specific guidance
        difficulty_guidance = {
            "beginner": "Assume no prior knowledge. Use simple language, avoid jargon, and explain all terms.",
            "intermediate": "Assume basic familiarity with the subject. Include practical applications and some technical depth.",
            "advanced": "Assume strong foundational knowledge. Focus on nuances, edge cases, and expert-level insights."
        }
        diff_guidance = difficulty_guidance.get(difficulty, difficulty_guidance["intermediate"])

        # Build the prompt
        if content:
            prompt = f"""You are an expert curriculum designer creating a {difficulty}-level course.

Topic: {topic}
Required chapters: exactly {num_chapters}
Content depth: {depth} ({depth_desc})
Time per chapter: {time_per_chapter} minutes

{diff_guidance}

IMPORTANT: If this is a recognized certification, professional credential, or standardized exam (e.g., CAPM, PMP, AWS, CISSP, etc.):
- Structure chapters based on the OFFICIAL exam domains/syllabus
- Use the actual certification curriculum as your guide
- Each chapter should align with real exam objectives
- Include domain names as they appear in the official certification guide

Based on this document, create exactly {num_chapters} chapters:

Document content:
{content}

Create chapters that:
- Progress logically from fundamentals to more complex concepts
- Are appropriate for {difficulty}-level learners
- Each can be studied in approximately {time_per_chapter} minutes
- Cover {depth}-level content

For each chapter provide:
- number: sequential (1 to {num_chapters})
- title: clear, descriptive title
- summary: 2-3 sentences explaining what the learner will gain
- key_concepts: 3-5 main ideas or skills covered
- difficulty: "{difficulty}"
- estimated_time_minutes: {time_per_chapter}

Return ONLY valid JSON:
{{
  "chapters": [
    {{
      "number": 1,
      "title": "Chapter Title",
      "summary": "What the learner will learn...",
      "key_concepts": ["concept1", "concept2", "concept3"],
      "difficulty": "{difficulty}",
      "estimated_time_minutes": {time_per_chapter}
    }}
  ]
}}"""
        else:
            prompt = f"""You are an expert curriculum designer creating a {difficulty}-level course.

Topic: {topic}
Required chapters: exactly {num_chapters}
Content depth: {depth} ({depth_desc})
Time per chapter: {time_per_chapter} minutes

{diff_guidance}

IMPORTANT: If this is a recognized certification, professional credential, or standardized exam (e.g., CAPM, PMP, AWS, CISSP, etc.):
- Structure chapters based on the OFFICIAL exam domains/syllabus
- Use the actual certification curriculum as your guide
- Each chapter should align with real exam objectives
- Include domain names as they appear in the official certification guide

Create exactly {num_chapters} chapters that:
- Progress logically from fundamentals to more complex concepts
- Are appropriate for {difficulty}-level learners
- Each can be studied in approximately {time_per_chapter} minutes
- Cover {depth}-level content

For each chapter provide:
- number: sequential (1 to {num_chapters})
- title: clear, descriptive title
- summary: 2-3 sentences explaining what the learner will gain
- key_concepts: 3-5 main ideas or skills covered
- difficulty: "{difficulty}"
- estimated_time_minutes: {time_per_chapter}

Return ONLY valid JSON:
{{
  "chapters": [
    {{
      "number": 1,
      "title": "Chapter Title",
      "summary": "What the learner will learn...",
      "key_concepts": ["concept1", "concept2", "concept3"],
      "difficulty": "{difficulty}",
      "estimated_time_minutes": {time_per_chapter}
    }}
  ]
}}"""

        # Call Gemini API
        start_time = llm_logger.log_request(self.default_model, prompt, "Chapter Generation")
        generation_config = genai.types.GenerationConfig(
            temperature=settings.temperature,
            max_output_tokens=settings.max_tokens_chapter,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, "Chapter Generation")

        # Log token usage - ALWAYS log, even if usage_metadata is missing
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        await self.log_token_usage(
            operation=OperationType.CHAPTER_GENERATION,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context or topic
        )

        # Parse response
        response_text = response.text

        # Extract JSON from response (handle markdown code blocks)
        json_text = self._parse_json_response(response_text)

        # Parse JSON
        data = json.loads(json_text) if isinstance(json_text, str) else json_text

        # Convert to Chapter objects
        chapters = [Chapter(**chapter) for chapter in data["chapters"]]

        return chapters

    def _map_difficulty(self, difficulty_str: str) -> QuestionDifficulty:
        """Map string difficulty to enum."""
        mapping = {
            "easy": QuestionDifficulty.EASY,
            "medium": QuestionDifficulty.MEDIUM,
            "hard": QuestionDifficulty.HARD,
        }
        return mapping.get(difficulty_str.lower(), QuestionDifficulty.MEDIUM)

    def _parse_json_response(self, response_text: str) -> str:
        """Extract JSON from response text."""
        json_text = response_text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
        return json_text

    async def generate_questions(
        self,
        chapter: Chapter,
        num_mcq: int = 5,
        num_true_false: int = 3
    ) -> Dict[str, Any]:
        """
        Generate quiz questions using Gemini AI (legacy method).

        Args:
            chapter: The chapter object
            num_mcq: Number of multiple choice questions
            num_true_false: Number of true/false questions

        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays
        """
        # Build config and delegate to the new method
        config = QuestionGenerationConfig(
            topic=chapter.title,
            difficulty=chapter.difficulty,
            audience=AUDIENCE_DESCRIPTIONS.get(chapter.difficulty, AUDIENCE_DESCRIPTIONS["intermediate"]),
            chapter_number=chapter.number,
            chapter_title=chapter.title,
            key_concepts=chapter.key_concepts,
            recommended_mcq_count=num_mcq,
            recommended_tf_count=num_true_false
        )

        chapter_questions = await self.generate_questions_from_config(config)

        # Convert back to legacy dict format
        return {
            "mcq": [
                {
                    "id": q.id,
                    "question": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty.value
                }
                for q in chapter_questions.mcq_questions
            ],
            "true_false": [
                {
                    "id": q.id,
                    "question": q.question_text,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty.value
                }
                for q in chapter_questions.true_false_questions
            ]
        }

    async def generate_questions_from_config(
        self,
        config: QuestionGenerationConfig,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> ChapterQuestions:
        """
        Generate quiz questions using full configuration.

        Args:
            config: QuestionGenerationConfig with all generation parameters
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            ChapterQuestions object with generated questions
        """
        key_concepts_str = ", ".join(config.key_concepts) if config.key_concepts else "General chapter concepts"

        # Determine question length guidance based on difficulty
        if config.difficulty == "beginner":
            length_guidance = "Keep questions SHORT (1-2 lines). Use simple vocabulary."
        elif config.difficulty == "advanced":
            length_guidance = "Scenario-based questions can be LONGER (3-8 lines). Use precise technical language."
        else:
            length_guidance = "Questions should be MODERATE length (2-4 lines). Balance clarity with depth."

        prompt = f"""You are an expert exam creator designing questions for {config.audience}.

Create questions for this chapter from a {config.difficulty} course on {config.topic}.

Chapter {config.chapter_number}: {config.chapter_title}
Key Concepts to Cover: {key_concepts_str}

Generate EXACTLY:
- {config.recommended_mcq_count} Multiple Choice Questions
- {config.recommended_tf_count} True/False Questions

RULES:
1. Language must be appropriate for {config.audience}
2. {length_guidance}
3. Cover ALL key concepts (at least 1 question per concept)
4. Mix difficulties: ~30% easy, ~50% medium, ~20% hard
5. MCQ options: exactly 4 options (A, B, C, D), one clearly correct, plausible distractors
6. NO trick questions or deliberately confusing wording
7. NO "All of the above" or "None of the above" options
8. Each question MUST have a clear explanation for the correct answer
9. True/False statements must be definitively true or false, not ambiguous

Return ONLY valid JSON (no markdown, no extra text):
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

        start_time = llm_logger.log_request(self.default_model, prompt, "Question Generation")
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=settings.max_tokens_question,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, "Question Generation")

        # Log token usage - ALWAYS log, even if usage_metadata is missing
        print(f"[GEMINI] QUESTION_GENERATION response received")
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0
        else:
            print(f"[GEMINI] WARNING: No usage_metadata for QUESTION_GENERATION")

        print(f"[GEMINI] About to call log_token_usage - user_id={user_id}, tokens={input_tokens}+{output_tokens}")
        await self.log_token_usage(
            operation=OperationType.QUESTION_GENERATION,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context or config.topic
        )
        print(f"[GEMINI] log_token_usage completed for QUESTION_GENERATION")

        # Parse response
        response_text = response.text
        json_text = self._parse_json_response(response_text)
        data = json.loads(json_text)

        # Create MCQ questions
        mcq_questions = []
        for item in data.get("mcq", []):
            try:
                mcq_questions.append(MCQQuestion(
                    id=str(uuid.uuid4()),
                    difficulty=self._map_difficulty(item.get("difficulty", "medium")),
                    question_text=item["question_text"],
                    options=item["options"],
                    correct_answer=item["correct_answer"],
                    explanation=item["explanation"],
                    points=1
                ))
            except Exception:
                continue

        # Create True/False questions
        tf_questions = []
        for item in data.get("true_false", []):
            try:
                tf_questions.append(TrueFalseQuestion(
                    id=str(uuid.uuid4()),
                    difficulty=self._map_difficulty(item.get("difficulty", "medium")),
                    question_text=item["question_text"],
                    correct_answer=bool(item["correct_answer"]),
                    explanation=item["explanation"],
                    points=1
                ))
            except Exception:
                continue

        return ChapterQuestions(
            chapter_number=config.chapter_number,
            chapter_title=config.chapter_title,
            mcq_questions=mcq_questions,
            true_false_questions=tf_questions
        )

    async def generate_feedback(
        self,
        user_progress: Dict[str, Any],
        weak_areas: List[str],
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate personalized feedback using Gemini AI.

        Args:
            user_progress: User's progress data
            weak_areas: Areas where student needs improvement
            user_id: User ID for token usage logging
            context: Context info for token logging

        Returns:
            Feedback message as string
        """
        prompt = f"""You are a supportive learning mentor.

Student Progress:
- Overall Score: {user_progress.get('overall_score', 0):.0%}
- Weak Areas: {', '.join(weak_areas) if weak_areas else 'None'}

Provide:
1. Encouraging feedback on progress
2. Specific areas to review
3. Study recommendations
4. Readiness assessment (ready/not ready for exam)

Be supportive but honest. Keep it concise (3-4 paragraphs)."""

        start_time = llm_logger.log_request(self.default_model, prompt, "Student Feedback")
        generation_config = genai.types.GenerationConfig(
            temperature=0.8,
            max_output_tokens=settings.max_tokens_feedback,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, "Student Feedback")

        # Log token usage - ALWAYS log
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        await self.log_token_usage(
            operation=OperationType.FEEDBACK_GENERATION,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context
        )

        return response.text

    async def check_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check answer using Gemini AI.

        Args:
            question: The question text
            user_answer: User's answer
            correct_answer: The correct answer
            user_id: User ID for token usage logging
            context: Context info for token logging

        Returns:
            Dictionary with 'is_correct', 'explanation', 'score'
        """
        prompt = f"""Evaluate this student's answer.

Question: {question}
Student Answer: {user_answer}
Correct Answer: {correct_answer}

Provide:
1. Is the answer correct? (true/false)
2. Explanation of why it's correct or incorrect
3. Score (1.0 for correct, 0.0 for incorrect, or partial credit 0.0-1.0)

Return ONLY valid JSON:
{{
  "is_correct": true/false,
  "explanation": "...",
  "score": 0.0-1.0
}}"""

        start_time = llm_logger.log_request(self.default_model, prompt, "Answer Checking")
        generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=settings.max_tokens_answer,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, "Answer Checking")

        # Log token usage - ALWAYS log
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        await self.log_token_usage(
            operation=OperationType.ANSWER_CHECK,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context
        )

        # Parse response
        response_text = response.text
        json_text = self._parse_json_response(response_text)

        return json.loads(json_text)

    async def answer_question(
        self,
        question: str,
        rag_context: str,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Answer student question using RAG context with Gemini AI.

        Args:
            question: Student's question
            rag_context: Relevant context from the material
            user_id: User ID for token usage logging
            context: Context info for token logging

        Returns:
            Answer as string
        """
        prompt = f"""You are a helpful tutor. Answer the student's question using the provided context.

Context from the learning material:
{rag_context}

Student's Question: {question}

Provide a clear, concise answer based on the context. If the context doesn't contain enough information, say so."""

        start_time = llm_logger.log_request(self.default_model, prompt, "RAG Query")
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=settings.max_tokens_rag,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, "RAG Query")

        # Log token usage - ALWAYS log
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        await self.log_token_usage(
            operation=OperationType.RAG_ANSWER,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context
        )

        return response.text

    async def analyze_document_structure(
        self,
        content: str,
        max_sections: int = 15,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> DocumentOutline:
        """
        Analyze document content and detect natural sections using Gemini AI.

        Args:
            content: Full extracted document text
            max_sections: Maximum number of sections to detect
            user_id: User ID for token usage logging
            context: Context info (filenames) for token logging

        Returns:
            DocumentOutline with detected structure
        """
        print(f"[GEMINI] analyze_document_structure called - user_id={user_id}, context={context}")
        # Truncate content if too long
        analysis_content = content[:50000]

        prompt = f"""Analyze this document and identify its natural sections/chapters.

DOCUMENT CONTENT:
{analysis_content}

INSTRUCTIONS:
1. Identify the document type (textbook, article, manual, notes, lecture, other)
2. Detect natural section breaks (headings, chapters, topic transitions)
3. For each section, identify:
   - A clear title (use document headings if present, or infer from content)
   - Key topics covered (3-7 topics per section)
   - Brief summary (1-2 sentences)
4. Return between 3 and {max_sections} sections based on document structure
5. DO NOT impose arbitrary divisions - follow the document's natural organization

IMPORTANT - SKIP these non-content sections (do NOT include them):
- Table of Contents
- Dedication
- Acknowledgments / Acknowledgements
- Foreword / Preface (unless it contains substantial educational content)
- Index
- Bibliography / References / Works Cited
- Appendices (unless they contain educational content worth studying)
- Copyright / Legal notices
- About the Author / Author Bio
- Glossary (unless it's substantial enough to be a learning resource)

Only include sections with actual educational/learning content that would make sense as course chapters.

Return ONLY valid JSON (no markdown, no extra text):
{{
  "document_title": "Main title of the document",
  "document_type": "textbook|article|manual|notes|lecture|other",
  "total_sections": <number>,
  "estimated_total_time_minutes": <number>,
  "analysis_notes": "Any notes about the document structure",
  "sections": [
    {{
      "order": 1,
      "title": "Section Title",
      "summary": "What this section covers...",
      "key_topics": ["topic1", "topic2", "topic3"],
      "confidence": 0.9
    }}
  ]
}}"""

        start_time = llm_logger.log_request(settings.model_document_analysis, prompt, "Document Analysis")
        generation_config = genai.types.GenerationConfig(
            temperature=0.5,
            max_output_tokens=settings.max_tokens_document_analysis,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, "Document Analysis")

        # Log token usage - ALWAYS log, even if usage_metadata is missing
        print(f"[GEMINI] ANALYZE_DOCUMENT response received")
        print(f"[GEMINI] Has usage_metadata: {hasattr(response, 'usage_metadata')}")

        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            print(f"[GEMINI] usage_metadata: {response.usage_metadata}")
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0
        else:
            print(f"[GEMINI] WARNING: No usage_metadata available, logging with 0 tokens")

        print(f"[GEMINI] About to call log_token_usage - user_id={user_id}, tokens={input_tokens}+{output_tokens}")
        await self.log_token_usage(
            operation=OperationType.ANALYZE_DOCUMENT,
            model=settings.model_document_analysis,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context
        )
        print(f"[GEMINI] log_token_usage completed for ANALYZE_DOCUMENT")

        # Parse response
        response_text = response.text
        json_text = self._parse_json_response(response_text)
        data = json.loads(json_text)

        # Create DetectedSection objects
        sections = [
            DetectedSection(
                order=s.get("order", i + 1),
                title=s["title"],
                summary=s.get("summary", ""),
                key_topics=s.get("key_topics", []),
                confidence=s.get("confidence", 0.8)
            )
            for i, s in enumerate(data.get("sections", []))
        ]

        return DocumentOutline(
            document_title=data.get("document_title", "Untitled Document"),
            document_type=data.get("document_type", "notes"),
            total_sections=len(sections),
            sections=sections,
            estimated_total_time_minutes=data.get("estimated_total_time_minutes", 60),
            analysis_notes=data.get("analysis_notes")
        )

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
        Generate detailed chapters based on user-confirmed outline using Gemini AI.
        Uses batch processing to handle large chapter counts without token limit issues.

        Args:
            topic: Course topic
            content: Full extracted document text
            confirmed_sections: User-confirmed sections
            difficulty: Course difficulty level
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            List of Chapter objects with key_ideas populated
        """
        # Filter to included sections only
        included_sections = [s for s in confirmed_sections if s.include]
        if not included_sections:
            included_sections = confirmed_sections[:1] if confirmed_sections else []

        # Truncate content if needed
        analysis_content = content[:40000]

        # Process in batches to avoid token limits (5 chapters per batch)
        BATCH_SIZE = 5
        all_chapters = []

        for batch_start in range(0, len(included_sections), BATCH_SIZE):
            batch_sections = included_sections[batch_start:batch_start + BATCH_SIZE]
            batch_chapters = await self._generate_chapter_batch(
                topic=topic,
                content=analysis_content,
                sections=batch_sections,
                difficulty=difficulty,
                start_number=batch_start + 1,
                user_id=user_id,
                context=context
            )
            all_chapters.extend(batch_chapters)

        return all_chapters

    async def _generate_chapter_batch(
        self,
        topic: str,
        content: str,
        sections: List[ConfirmedSection],
        difficulty: str,
        start_number: int,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[Chapter]:
        """
        Generate a batch of chapters (max 5 at a time) to stay within token limits.

        Args:
            topic: Course topic
            content: Document content (already truncated)
            sections: Batch of sections to generate
            difficulty: Course difficulty level
            start_number: Starting chapter number for this batch
            user_id: User ID for token usage logging
            context: Context info (topic/filenames) for token logging

        Returns:
            List of Chapter objects for this batch
        """
        # Build sections info for this batch
        sections_info = "\n".join([
            f"Chapter {start_number + i}: {s.title}\n  Topics: {', '.join(s.key_topics)}"
            for i, s in enumerate(sections)
        ])

        # Difficulty-specific guidance
        difficulty_guidance = {
            "beginner": "Use simple language, avoid jargon, and explain all terms.",
            "intermediate": "Include practical applications and some technical depth.",
            "advanced": "Focus on nuances, edge cases, and expert-level insights."
        }
        diff_guidance = difficulty_guidance.get(difficulty, difficulty_guidance["intermediate"])

        # Time per chapter
        time_map = {"beginner": 25, "intermediate": 45, "advanced": 90}
        time_per_chapter = time_map.get(difficulty, 45)

        end_number = start_number + len(sections) - 1
        prompt = f"""Create detailed chapter content for chapters {start_number} to {end_number} of this {difficulty}-level course.

TOPIC: {topic}

CHAPTERS TO GENERATE (exactly {len(sections)} chapters):
{sections_info}

DOCUMENT CONTENT:
{content}

{diff_guidance}

For EACH chapter listed above, generate:
- number: Use the chapter number specified above ({start_number} to {end_number})
- title: Use the chapter title provided
- summary: 2-3 sentences explaining what learner will gain
- key_concepts: 3-5 main concepts/skills (high-level)
- key_ideas: 5-10 SPECIFIC testable statements (granular, for question generation)
- source_excerpt: 1-2 key sentences from the source content
- difficulty: "{difficulty}"
- estimated_time_minutes: {time_per_chapter}

IMPORTANT: key_ideas must be specific, testable facts from the content.

Return ONLY valid JSON (no markdown, no extra text):
{{
  "chapters": [
    {{
      "number": {start_number},
      "title": "Chapter Title",
      "summary": "What the learner will learn...",
      "key_concepts": ["concept1", "concept2"],
      "key_ideas": ["Specific fact 1", "Specific fact 2", "..."],
      "source_excerpt": "Key quote from source...",
      "difficulty": "{difficulty}",
      "estimated_time_minutes": {time_per_chapter}
    }}
  ]
}}"""

        start_time = llm_logger.log_request(self.default_model, prompt, f"Chapter Batch {start_number}-{end_number}")
        generation_config = genai.types.GenerationConfig(
            temperature=settings.temperature,
            max_output_tokens=settings.max_tokens_chapter,
        )
        response = await self.model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        llm_logger.log_response(start_time, f"Chapter Batch {start_number}-{end_number}")

        # Log token usage - ALWAYS log
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        await self.log_token_usage(
            operation=OperationType.CHAPTER_GENERATION,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            user_id=user_id,
            context=context or topic
        )

        # Parse response
        response_text = response.text
        json_text = self._parse_json_response(response_text)
        data = json.loads(json_text)

        # Convert to Chapter objects
        chapters = [Chapter(**chapter) for chapter in data.get("chapters", [])]

        return chapters

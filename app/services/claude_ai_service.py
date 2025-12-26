"""
Claude AI Service
Real implementation using Anthropic's Claude API.
Implements BaseAIService interface.
"""
from typing import List, Dict, Any
import json
from anthropic import Anthropic, AsyncAnthropic
from app.models.course import Chapter
from app.services.base_ai_service import BaseAIService
from app.config import settings


class ClaudeAIService(BaseAIService):
    """
    Claude AI service for production use.
    Makes actual API calls to Anthropic's Claude models.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize Claude AI service.
        
        Args:
            model: Optional model override. If not provided, uses config defaults.
        """
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.default_model = model or settings.model_chapter_generation
    
    async def generate_chapters(self, topic: str, difficulty: str = "intermediate", content: str = "") -> List[Chapter]:
        """
        Generate chapters using Claude AI.

        Args:
            topic: The subject/topic for the course
            difficulty: Difficulty level for all chapters (beginner/intermediate/advanced)
            content: Optional document content to analyze

        Returns:
            List of Chapter objects
        """
        # Build the prompt
        if content:
            prompt = f"""You are an expert educational content creator.

Given this document about {topic}, break it down into logical chapters.
All chapters must be at the "{difficulty}" difficulty level.

Document content:
{content}

For each chapter, provide:
1. Chapter number
2. Title (concise, clear)
3. Summary (2-3 sentences)
4. Key concepts (list of 3-5 main ideas)
5. Difficulty: always set to "{difficulty}"

Return ONLY valid JSON in this format:
{{
  "chapters": [
    {{
      "number": 1,
      "title": "...",
      "summary": "...",
      "key_concepts": [...],
      "difficulty": "{difficulty}"
    }}
  ]
}}"""
        else:
            prompt = f"""You are an expert educational content creator.

Create a structured course about {topic} with logical chapters.
All chapters must be at the "{difficulty}" difficulty level.

For each chapter, provide:
1. Chapter number
2. Title (concise, clear)
3. Summary (2-3 sentences)
4. Key concepts (list of 3-5 main ideas)
5. Difficulty: always set to "{difficulty}"

Create 4-6 chapters that progressively build knowledge, all at the {difficulty} level.

Return ONLY valid JSON in this format:
{{
  "chapters": [
    {{
      "number": 1,
      "title": "...",
      "summary": "...",
      "key_concepts": [...],
      "difficulty": "{difficulty}"
    }}
  ]
}}"""
        
        # Call Claude API
        response = await self.client.messages.create(
            model=self.default_model,
            max_tokens=settings.max_tokens_chapter,
            temperature=settings.temperature,
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
        
        # Parse JSON
        data = json.loads(json_text)
        
        # Convert to Chapter objects
        chapters = [Chapter(**chapter) for chapter in data["chapters"]]
        
        return chapters
    
    async def generate_questions(
        self, 
        chapter: Chapter, 
        num_mcq: int = 5, 
        num_true_false: int = 3
    ) -> Dict[str, Any]:
        """
        Generate quiz questions using Claude AI.
        
        Args:
            chapter: The chapter object
            num_mcq: Number of multiple choice questions
            num_true_false: Number of true/false questions
            
        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays
        """
        prompt = f"""Create assessment questions for this chapter.

Chapter: {chapter.title}
Summary: {chapter.summary}
Key Concepts: {', '.join(chapter.key_concepts)}
Difficulty: {chapter.difficulty}

Generate:
- {num_mcq} multiple choice questions (4 options each, one correct)
- {num_true_false} true/false questions

For each question include:
1. Question text
2. Options (for MCQ)
3. Correct answer
4. Explanation (why this answer is correct)
5. Difficulty level (easy/medium/hard)

Return ONLY valid JSON:
{{
  "mcq": [
    {{
      "id": "mcq_1",
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "A",
      "explanation": "...",
      "difficulty": "medium"
    }}
  ],
  "true_false": [
    {{
      "id": "tf_1",
      "question": "...",
      "correct_answer": true,
      "explanation": "...",
      "difficulty": "easy"
    }}
  ]
}}"""
        
        response = await self.client.messages.create(
            model=settings.model_question_generation,
            max_tokens=settings.max_tokens_question,
            temperature=settings.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        response_text = response.content[0].text
        
        # Extract JSON
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(json_text)
    
    async def generate_feedback(
        self, 
        user_progress: Dict[str, Any],
        weak_areas: List[str]
    ) -> str:
        """
        Generate personalized feedback using Claude AI.
        
        Args:
            user_progress: User's progress data
            weak_areas: Areas where student needs improvement
            
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
        
        response = await self.client.messages.create(
            model=settings.model_student_feedback,
            max_tokens=settings.max_tokens_feedback,
            temperature=0.8,  # Slightly higher for more personalized responses
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def check_answer(
        self, 
        question: str, 
        user_answer: str, 
        correct_answer: str
    ) -> Dict[str, Any]:
        """
        Check answer using Claude AI.
        
        Args:
            question: The question text
            user_answer: User's answer
            correct_answer: The correct answer
            
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
        
        response = await self.client.messages.create(
            model=settings.model_answer_checking,
            max_tokens=settings.max_tokens_answer,
            temperature=0.3,  # Lower for more consistent evaluation
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        response_text = response.content[0].text
        
        # Extract JSON
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(json_text)
    
    async def answer_question(
        self, 
        question: str, 
        context: str
    ) -> str:
        """
        Answer student question using RAG context with Claude AI.
        
        Args:
            question: Student's question
            context: Relevant context from the material
            
        Returns:
            Answer as string
        """
        prompt = f"""You are a helpful tutor. Answer the student's question using the provided context.

Context from the learning material:
{context}

Student's Question: {question}

Provide a clear, concise answer based on the context. If the context doesn't contain enough information, say so."""
        
        response = await self.client.messages.create(
            model=settings.model_rag_query,
            max_tokens=settings.max_tokens_rag,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
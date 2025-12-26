"""
Mock AI Service
Simulates AI responses without making actual API calls.
Implements BaseAIService interface.
"""
from typing import List, Dict, Any
from app.models.course import Chapter
from app.services.base_ai_service import BaseAIService


class MockAIService(BaseAIService):
    """
    Mock AI service for testing and development.
    Returns predefined responses without calling external APIs.
    """
    
    def __init__(self):
        self.mock_chapters_data = {
            "project management": [
                {
                    "number": 1,
                    "title": "Introduction to Project Management",
                    "summary": "Learn the fundamentals of project management including planning, execution, and monitoring. Understand the role of a project manager and key responsibilities.",
                    "key_concepts": ["Project lifecycle", "Stakeholder management", "Project charter", "Scope definition"],
                    "difficulty": "beginner"
                },
                {
                    "number": 2,
                    "title": "Project Planning and Scheduling",
                    "summary": "Master the art of creating effective project plans, timelines, and schedules. Learn about critical path method and resource allocation.",
                    "key_concepts": ["Work Breakdown Structure (WBS)", "Gantt charts", "Critical path", "Resource leveling"],
                    "difficulty": "intermediate"
                },
                {
                    "number": 3,
                    "title": "Risk Management and Quality Control",
                    "summary": "Identify, assess, and mitigate project risks. Implement quality assurance and control measures throughout the project lifecycle.",
                    "key_concepts": ["Risk identification", "Risk mitigation strategies", "Quality metrics", "Continuous improvement"],
                    "difficulty": "intermediate"
                },
                {
                    "number": 4,
                    "title": "Agile and Scrum Methodologies",
                    "summary": "Explore modern agile frameworks including Scrum, Kanban, and lean principles. Learn how to implement iterative development.",
                    "key_concepts": ["Scrum framework", "Sprint planning", "User stories", "Daily standups"],
                    "difficulty": "advanced"
                }
            ],
            "python programming": [
                {
                    "number": 1,
                    "title": "Python Basics and Syntax",
                    "summary": "Get started with Python programming. Learn variables, data types, operators, and basic control structures.",
                    "key_concepts": ["Variables and data types", "Operators", "If-else statements", "Loops"],
                    "difficulty": "beginner"
                },
                {
                    "number": 2,
                    "title": "Functions and Modules",
                    "summary": "Master Python functions, parameters, return values, and how to organize code using modules and packages.",
                    "key_concepts": ["Function definition", "Parameters and arguments", "Lambda functions", "Importing modules"],
                    "difficulty": "beginner"
                },
                {
                    "number": 3,
                    "title": "Object-Oriented Programming",
                    "summary": "Learn OOP concepts in Python including classes, objects, inheritance, and polymorphism.",
                    "key_concepts": ["Classes and objects", "Inheritance", "Encapsulation", "Magic methods"],
                    "difficulty": "intermediate"
                },
                {
                    "number": 4,
                    "title": "File Handling and Exception Management",
                    "summary": "Work with files, handle exceptions gracefully, and implement proper error handling in your programs.",
                    "key_concepts": ["File operations", "Try-except blocks", "Custom exceptions", "Context managers"],
                    "difficulty": "intermediate"
                }
            ],
            "default": [
                {
                    "number": 1,
                    "title": "Introduction and Fundamentals",
                    "summary": "Explore the basic concepts and foundational principles of the subject. Build a strong understanding of core terminology.",
                    "key_concepts": ["Core concepts", "Terminology", "Historical context", "Basic principles"],
                    "difficulty": "beginner"
                },
                {
                    "number": 2,
                    "title": "Intermediate Concepts and Applications",
                    "summary": "Dive deeper into practical applications and real-world examples. Learn intermediate techniques and methodologies.",
                    "key_concepts": ["Practical applications", "Case studies", "Problem-solving", "Best practices"],
                    "difficulty": "intermediate"
                },
                {
                    "number": 3,
                    "title": "Advanced Topics and Mastery",
                    "summary": "Master advanced concepts and expert-level techniques. Prepare for professional application of knowledge.",
                    "key_concepts": ["Advanced techniques", "Expert strategies", "Industry standards", "Future trends"],
                    "difficulty": "advanced"
                }
            ]
        }
    
    async def generate_chapters(self, topic: str, difficulty: str = "intermediate", content: str = "") -> List[Chapter]:
        """
        Generate mock chapters for a given topic.

        Args:
            topic: The subject/topic for the course
            difficulty: Difficulty level for all chapters (beginner/intermediate/advanced)
            content: Optional document content (ignored in mock)

        Returns:
            List of Chapter objects
        """
        # Normalize the topic
        normalized_topic = topic.lower().strip()

        # Get mock data for this topic, or use default
        chapter_data = self.mock_chapters_data.get(
            normalized_topic,
            self.mock_chapters_data["default"]
        )

        # Convert dictionaries to Chapter objects with user-specified difficulty
        chapters = []
        for chapter in chapter_data:
            chapter_with_difficulty = {**chapter, "difficulty": difficulty}
            chapters.append(Chapter(**chapter_with_difficulty))

        return chapters
    
    async def generate_questions(
        self, 
        chapter: Chapter, 
        num_mcq: int = 5, 
        num_true_false: int = 3
    ) -> Dict[str, Any]:
        """
        Generate mock quiz questions for a chapter.
        
        Args:
            chapter: The chapter object
            num_mcq: Number of multiple choice questions
            num_true_false: Number of true/false questions
            
        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays
        """
        mcq_questions = [
            {
                "id": f"mcq_{i+1}",
                "question": f"What is an important concept in {chapter.title}? (Question {i+1})",
                "options": [
                    f"A) {chapter.key_concepts[0] if chapter.key_concepts else 'Option A'}",
                    "B) An incorrect option",
                    "C) Another incorrect option",
                    "D) Yet another incorrect option"
                ],
                "correct_answer": "A",
                "explanation": f"Option A is correct because it relates to {chapter.key_concepts[0] if chapter.key_concepts else 'the key concept'}.",
                "difficulty": chapter.difficulty
            }
            for i in range(num_mcq)
        ]
        
        true_false_questions = [
            {
                "id": f"tf_{i+1}",
                "question": f"The concept of {chapter.key_concepts[i] if i < len(chapter.key_concepts) else 'this topic'} is important in {chapter.title}.",
                "correct_answer": True,
                "explanation": f"This statement is true because {chapter.key_concepts[i] if i < len(chapter.key_concepts) else 'this concept'} is a fundamental part of the chapter.",
                "difficulty": chapter.difficulty
            }
            for i in range(num_true_false)
        ]
        
        return {
            "mcq": mcq_questions,
            "true_false": true_false_questions
        }
    
    async def generate_feedback(
        self, 
        user_progress: Dict[str, Any],
        weak_areas: List[str]
    ) -> str:
        """
        Generate mock personalized feedback.
        
        Args:
            user_progress: User's progress data
            weak_areas: Areas where student needs improvement
            
        Returns:
            Feedback message as string
        """
        overall_score = user_progress.get("overall_score", 0)
        
        if overall_score >= 0.8:
            tone = "Excellent work!"
        elif overall_score >= 0.6:
            tone = "Good progress!"
        else:
            tone = "Keep working hard!"
        
        weak_areas_text = ", ".join(weak_areas) if weak_areas else "none identified"
        
        feedback = f"""{tone} You've achieved a {overall_score:.0%} overall score.

Areas needing attention: {weak_areas_text}

Recommendations:
1. Review the material in your weaker areas
2. Practice with additional questions
3. Take your time to understand the concepts

You're making progress! Keep it up!"""
        
        return feedback
    
    async def check_answer(
        self, 
        question: str, 
        user_answer: str, 
        correct_answer: str
    ) -> Dict[str, Any]:
        """
        Mock answer checking.
        
        Args:
            question: The question text
            user_answer: User's answer
            correct_answer: The correct answer
            
        Returns:
            Dictionary with 'is_correct', 'explanation', 'score'
        """
        is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()
        
        return {
            "is_correct": is_correct,
            "explanation": f"The correct answer is {correct_answer}. {'Well done!' if is_correct else 'Keep studying!'}",
            "score": 1.0 if is_correct else 0.0
        }
    
    async def answer_question(
        self, 
        question: str, 
        context: str
    ) -> str:
        """
        Mock RAG question answering.
        
        Args:
            question: Student's question
            context: Relevant context from the material
            
        Returns:
            Answer as string
        """
        return f"Based on the material, here's the answer to your question: {question}\n\n[Mock answer would be generated here using the provided context]"
    
    def get_supported_topics(self) -> List[str]:
        """Get list of topics that have specific mock data."""
        return [topic for topic in self.mock_chapters_data.keys() if topic != "default"]
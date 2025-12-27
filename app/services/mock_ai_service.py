"""
Mock AI Service
Simulates AI responses without making actual API calls.
Implements BaseAIService interface.
"""
import uuid
import random
from typing import List, Dict, Any
from app.models.course import Chapter, CourseConfig
from app.models.question import (
    QuestionGenerationConfig,
    ChapterQuestions,
    MCQQuestion,
    TrueFalseQuestion,
    QuestionDifficulty,
)
from app.services.base_ai_service import BaseAIService


class MockAIService(BaseAIService):
    """
    Mock AI service for testing and development.
    Returns predefined responses without calling external APIs.
    """

    def __init__(self):
        # Difficulty-specific chapter templates
        self.difficulty_templates = {
            "beginner": {
                "title_prefix": "Introduction to",
                "summary_style": "Learn the basics of {concept}. This chapter covers fundamental concepts in simple, easy-to-understand terms.",
                "concepts_suffix": ["basics", "fundamentals", "getting started"],
            },
            "intermediate": {
                "title_prefix": "Working with",
                "summary_style": "Dive deeper into {concept} with practical examples and hands-on exercises. Apply your knowledge to real-world scenarios.",
                "concepts_suffix": ["best practices", "practical applications", "real-world examples"],
            },
            "advanced": {
                "title_prefix": "Mastering",
                "summary_style": "Explore advanced {concept} techniques and expert-level patterns. Learn optimization strategies and edge cases.",
                "concepts_suffix": ["advanced patterns", "optimization", "expert techniques"],
            },
        }

        # Topic-specific chapter data (keyed by normalized topic)
        self.topic_data = {
            "project management": {
                "subtopics": [
                    "Project Fundamentals",
                    "Planning and Scheduling",
                    "Resource Management",
                    "Risk Assessment",
                    "Quality Control",
                    "Agile Methodologies",
                    "Stakeholder Communication",
                    "Project Closure",
                    "Leadership Skills",
                    "Tools and Software",
                    "Budget Management",
                    "Team Dynamics",
                ],
                "concepts": [
                    ["Project lifecycle", "Stakeholder identification", "Project charter", "Scope definition"],
                    ["Work Breakdown Structure", "Gantt charts", "Critical path", "Milestones"],
                    ["Resource allocation", "Team building", "Capacity planning", "Skills matrix"],
                    ["Risk identification", "Risk mitigation", "Contingency planning", "SWOT analysis"],
                    ["Quality metrics", "Process improvement", "KPIs", "Auditing"],
                    ["Scrum framework", "Sprint planning", "User stories", "Retrospectives"],
                    ["Communication plan", "Status reporting", "Meeting facilitation", "Conflict resolution"],
                    ["Lessons learned", "Documentation", "Handover", "Post-project review"],
                    ["Team motivation", "Decision making", "Delegation", "Mentoring"],
                    ["MS Project", "Jira", "Trello", "Collaboration tools"],
                    ["Cost estimation", "Budget tracking", "Variance analysis", "Financial reporting"],
                    ["Team roles", "Collaboration", "Remote teams", "Performance management"],
                ],
            },
            "python programming": {
                "subtopics": [
                    "Python Basics",
                    "Data Types and Variables",
                    "Control Flow",
                    "Functions",
                    "Object-Oriented Programming",
                    "File Handling",
                    "Error Handling",
                    "Modules and Packages",
                    "Data Structures",
                    "Decorators and Generators",
                    "Testing",
                    "Web Development",
                ],
                "concepts": [
                    ["Syntax", "Indentation", "Comments", "Print statements"],
                    ["Strings", "Numbers", "Lists", "Dictionaries"],
                    ["If statements", "For loops", "While loops", "Comprehensions"],
                    ["Function definition", "Parameters", "Return values", "Lambda functions"],
                    ["Classes", "Objects", "Inheritance", "Polymorphism"],
                    ["Reading files", "Writing files", "CSV handling", "JSON parsing"],
                    ["Try-except", "Custom exceptions", "Logging", "Debugging"],
                    ["Importing", "Creating modules", "Package structure", "Virtual environments"],
                    ["Lists", "Tuples", "Sets", "Dictionaries"],
                    ["Decorators", "Generators", "Context managers", "Iterators"],
                    ["Unit testing", "pytest", "Mocking", "Test coverage"],
                    ["Flask", "FastAPI", "APIs", "Databases"],
                ],
            },
        }

        # Default subtopics for unknown topics
        self.default_data = {
            "subtopics": [
                "Fundamentals",
                "Core Concepts",
                "Practical Applications",
                "Best Practices",
                "Tools and Techniques",
                "Advanced Topics",
                "Case Studies",
                "Industry Standards",
                "Future Trends",
                "Professional Development",
                "Problem Solving",
                "Integration",
            ],
            "concepts": [
                ["Basic principles", "Key terminology", "Historical background", "Core ideas"],
                ["Main concepts", "Relationships", "Frameworks", "Models"],
                ["Real-world use", "Examples", "Implementation", "Practical tips"],
                ["Standards", "Guidelines", "Recommendations", "Common patterns"],
                ["Popular tools", "Methodologies", "Workflows", "Automation"],
                ["Complex topics", "Edge cases", "Optimization", "Scalability"],
                ["Success stories", "Lessons learned", "Analysis", "Comparisons"],
                ["Certifications", "Regulations", "Compliance", "Quality standards"],
                ["Emerging trends", "Innovation", "Research", "Predictions"],
                ["Career paths", "Skills development", "Networking", "Continuous learning"],
                ["Analytical thinking", "Troubleshooting", "Root cause analysis", "Solutions"],
                ["Cross-functional", "Collaboration", "Systems thinking", "Holistic approach"],
            ],
        }

        # Question templates by difficulty
        self.mcq_templates = {
            "beginner": [
                "What is {concept}?",
                "Which of the following best describes {concept}?",
                "What is the main purpose of {concept}?",
                "Which statement about {concept} is correct?",
            ],
            "intermediate": [
                "How does {concept} relate to {topic}?",
                "What is the best approach when implementing {concept}?",
                "Which of the following is a key benefit of {concept}?",
                "In the context of {topic}, what role does {concept} play?",
            ],
            "advanced": [
                "When optimizing {concept} in {topic}, which strategy is most effective?",
                "What are the trade-offs when applying {concept} in complex {topic} scenarios?",
                "How would you troubleshoot issues related to {concept} in production?",
                "Which advanced technique best leverages {concept} for enterprise {topic}?",
            ],
        }

        self.tf_templates = {
            "beginner": [
                "{concept} is a fundamental part of {topic}.",
                "Understanding {concept} is essential for beginners in {topic}.",
                "{concept} helps improve outcomes in {topic}.",
            ],
            "intermediate": [
                "{concept} should always be considered when working with {topic}.",
                "Proper implementation of {concept} can significantly improve {topic} results.",
                "{concept} is only relevant in advanced {topic} scenarios.",
            ],
            "advanced": [
                "In enterprise environments, {concept} requires specialized handling.",
                "{concept} performance can be optimized through caching strategies.",
                "Modern {topic} implementations rarely use {concept}.",
            ],
        }

        # Difficulty distribution: 30% easy, 50% medium, 20% hard
        self.difficulty_weights = {
            "beginner": [0.5, 0.4, 0.1],  # More easy
            "intermediate": [0.3, 0.5, 0.2],  # Balanced
            "advanced": [0.1, 0.4, 0.5],  # More hard
        }

    async def generate_chapters(
        self,
        topic: str,
        config: CourseConfig,
        content: str = ""
    ) -> List[Chapter]:
        """
        Generate mock chapters for a given topic.

        Args:
            topic: The subject/topic for the course
            config: CourseConfig with chapter count, difficulty, depth, and time settings
            content: Optional document content (ignored in mock)

        Returns:
            List of Chapter objects
        """
        normalized_topic = topic.lower().strip()
        num_chapters = config.recommended_chapters
        difficulty = config.difficulty
        time_per_chapter = config.time_per_chapter_minutes
        depth = config.chapter_depth

        # Get topic-specific data or defaults
        topic_info = self.topic_data.get(normalized_topic, self.default_data)
        subtopics = topic_info["subtopics"]
        all_concepts = topic_info["concepts"]

        # Get difficulty template
        template = self.difficulty_templates.get(difficulty, self.difficulty_templates["intermediate"])

        chapters = []
        for i in range(num_chapters):
            # Cycle through subtopics if needed
            subtopic_index = i % len(subtopics)
            subtopic = subtopics[subtopic_index]

            # Get concepts for this chapter
            base_concepts = all_concepts[subtopic_index] if subtopic_index < len(all_concepts) else all_concepts[0]

            # Adjust title based on difficulty
            if difficulty == "beginner":
                title = f"Introduction to {subtopic}"
            elif difficulty == "advanced":
                title = f"Advanced {subtopic}"
            else:
                title = f"{subtopic}"

            # Add chapter number prefix for clarity
            if i >= len(subtopics):
                title = f"{subtopic} - Part {(i // len(subtopics)) + 1}"

            # Generate summary based on difficulty and depth
            if depth == "overview":
                summary = f"Get a high-level overview of {subtopic.lower()}. Learn the essential concepts and terminology needed to understand this area of {topic}."
            elif depth == "comprehensive":
                summary = f"Master {subtopic.lower()} with in-depth coverage of advanced techniques. Explore expert-level concepts, edge cases, and professional best practices in {topic}."
            else:  # detailed
                summary = f"Develop practical skills in {subtopic.lower()}. This chapter covers key concepts with hands-on examples and real-world applications in {topic}."

            # Adjust concepts for difficulty
            adjusted_concepts = base_concepts[:4]  # Take first 4 base concepts
            if difficulty == "beginner":
                adjusted_concepts = [f"{c} basics" if "basic" not in c.lower() else c for c in adjusted_concepts[:3]]
                adjusted_concepts.append("Getting started")
            elif difficulty == "advanced":
                adjusted_concepts = [f"Advanced {c.lower()}" if "advanced" not in c.lower() else c for c in adjusted_concepts]

            chapter_data = {
                "number": i + 1,
                "title": title,
                "summary": summary,
                "key_concepts": adjusted_concepts,
                "difficulty": difficulty,
                "estimated_time_minutes": time_per_chapter
            }
            chapters.append(Chapter(**chapter_data))

        return chapters

    def _get_question_difficulty(self, course_difficulty: str) -> QuestionDifficulty:
        """Get a weighted random question difficulty based on course difficulty."""
        weights = self.difficulty_weights.get(course_difficulty, self.difficulty_weights["intermediate"])
        difficulties = [QuestionDifficulty.EASY, QuestionDifficulty.MEDIUM, QuestionDifficulty.HARD]
        return random.choices(difficulties, weights=weights)[0]

    def _generate_mcq_options(self, concept: str, correct_idx: int = 0) -> List[str]:
        """Generate 4 MCQ options with the correct one at the specified index."""
        options = [
            f"A correct definition or description of {concept}",
            f"A common misconception about {concept}",
            f"An unrelated concept that sounds similar",
            f"A partially correct but incomplete statement",
        ]
        # Shuffle and ensure correct answer is at the right position
        correct = options[0]
        wrong = options[1:]
        random.shuffle(wrong)
        result = wrong[:correct_idx] + [correct] + wrong[correct_idx:]
        letters = ["A", "B", "C", "D"]
        return [f"{letters[i]}) {opt}" for i, opt in enumerate(result[:4])]

    async def generate_questions(
        self,
        chapter: Chapter,
        num_mcq: int = 5,
        num_true_false: int = 3
    ) -> Dict[str, Any]:
        """
        Generate mock quiz questions for a chapter (legacy method).

        Args:
            chapter: The chapter object
            num_mcq: Number of multiple choice questions
            num_true_false: Number of true/false questions

        Returns:
            Dictionary with 'mcq' and 'true_false' question arrays
        """
        config = QuestionGenerationConfig(
            topic=chapter.title,
            difficulty=chapter.difficulty,
            audience="general learners",
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
        config: QuestionGenerationConfig
    ) -> ChapterQuestions:
        """
        Generate realistic mock questions based on configuration.

        Args:
            config: QuestionGenerationConfig with all generation parameters

        Returns:
            ChapterQuestions object with generated questions
        """
        mcq_questions = []
        tf_questions = []

        # Get concepts to use (cycle through if needed)
        concepts = config.key_concepts if config.key_concepts else ["key concept", "main idea", "core principle"]
        templates = self.mcq_templates.get(config.difficulty, self.mcq_templates["intermediate"])
        tf_templates = self.tf_templates.get(config.difficulty, self.tf_templates["intermediate"])

        # Generate MCQ questions
        for i in range(config.recommended_mcq_count):
            concept = concepts[i % len(concepts)]
            template = templates[i % len(templates)]
            question_text = template.format(concept=concept, topic=config.topic)
            difficulty = self._get_question_difficulty(config.difficulty)
            correct_idx = random.randint(0, 3)
            correct_letter = ["A", "B", "C", "D"][correct_idx]

            mcq_questions.append(MCQQuestion(
                id=str(uuid.uuid4()),
                difficulty=difficulty,
                question_text=question_text,
                options=self._generate_mcq_options(concept, correct_idx),
                correct_answer=correct_letter,
                explanation=f"The correct answer is {correct_letter} because {concept} is essential to understanding {config.chapter_title}. This concept directly relates to the practical application of {config.topic}.",
                points=1
            ))

        # Generate True/False questions
        for i in range(config.recommended_tf_count):
            concept = concepts[i % len(concepts)]
            template = tf_templates[i % len(tf_templates)]
            question_text = template.format(concept=concept, topic=config.topic)
            difficulty = self._get_question_difficulty(config.difficulty)
            # Alternate true/false with some randomness
            correct_answer = random.choice([True, True, False])  # 2/3 true bias

            tf_questions.append(TrueFalseQuestion(
                id=str(uuid.uuid4()),
                difficulty=difficulty,
                question_text=question_text,
                correct_answer=correct_answer,
                explanation=f"This statement is {'true' if correct_answer else 'false'}. {concept} {'is indeed' if correct_answer else 'is not necessarily'} a key aspect of {config.topic} as covered in {config.chapter_title}.",
                points=1
            ))

        return ChapterQuestions(
            chapter_number=config.chapter_number,
            chapter_title=config.chapter_title,
            mcq_questions=mcq_questions,
            true_false_questions=tf_questions
        )

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
        return list(self.topic_data.keys())

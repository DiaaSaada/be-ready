# CLAUDE.md - AI Learning Platform

## Project Overview

An AI-powered learning platform backend built with FastAPI. The system takes topics or PDF materials, validates them, breaks them into chapters using AI (Claude/OpenAI/Gemini), generates quiz questions, tracks user progress, and provides personalized mentoring feedback.

## Tech Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: MongoDB with Motor (async driver)
- **AI Providers**: Anthropic Claude, OpenAI GPT, Google Gemini, Mock (for testing)
- **PDF Processing**: PyPDF2, PyMuPDF - NOT YET IMPLEMENTED
- **Validation**: Pydantic v2

## Project Structure

```
be-ready/
├── app/
│   ├── __init__.py
│   ├── config.py                  # Pydantic Settings, AI provider config
│   ├── main.py                    # FastAPI app entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── course.py              # Chapter, Course, CourseConfig models
│   │   ├── question.py            # MCQQuestion, TrueFalseQuestion, ChapterQuestions
│   │   ├── validation.py          # TopicValidationResult, TopicComplexity
│   │   ├── user.py                # User models (UserCreate, UserInDB, etc.)
│   │   └── responses.py           # API response models (CourseSummary, MyCoursesResponse)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_ai_service.py     # Abstract base class (interface)
│   │   ├── ai_service_factory.py  # Factory pattern for provider selection
│   │   ├── mock_ai_service.py     # Mock implementation
│   │   ├── claude_ai_service.py   # Anthropic Claude implementation
│   │   ├── openai_ai_service.py   # OpenAI GPT implementation
│   │   ├── gemini_ai_service.py   # Google Gemini implementation
│   │   ├── topic_validator.py     # Topic validation service
│   │   ├── course_configurator.py # Course structure configuration
│   │   ├── question_analyzer.py   # AI-based question count analysis
│   │   ├── question_generator.py  # Question generation orchestrator
│   │   └── auth_service.py        # Password hashing, JWT tokens
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── courses.py             # Course generation endpoints
│   │   ├── questions.py           # Question generation endpoints
│   │   ├── progress.py            # Progress tracking endpoints
│   │   └── my_courses.py          # Enrolled courses endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py          # MongoDB connection management
│   │   ├── models.py              # Document models
│   │   ├── crud.py                # Database operations
│   │   └── user_repository.py     # User CRUD operations
│   ├── dependencies/
│   │   └── auth.py                # get_current_user dependency
│   └── utils/
│       └── __init__.py
├── tests/
├── uploads/
├── logs/                          # Failed AI response logs for debugging
├── scripts/
│   └── check_mongodb.py           # MongoDB utility script
├── .env
├── .env.example
├── requirements.txt
├── requirements-minimal.txt
├── test_api.py                    # API test suite
└── run.py                         # Application runner
```

## Commands

```bash
# Run the development server
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload

# Install dependencies
pip install -r requirements-minimal.txt

# Run API tests
python test_api.py
```

## Utility Scripts

Located in `scripts/` folder for database inspection and debugging.

### MongoDB Check Script

```bash
# List all collections with document counts
python scripts/check_mongodb.py

# Show documents from a specific collection (default 5)
python scripts/check_mongodb.py courses
python scripts/check_mongodb.py questions
python scripts/check_mongodb.py question_batches

# Show more documents
python scripts/check_mongodb.py questions 10

# Show all collections with sample documents
python scripts/check_mongodb.py --all
```

**Collections:**
- `courses` - User-linked courses (by user_id, topic + difficulty)
- `questions` - Cached generated questions (by topic + difficulty + chapter)
- `question_batches` - Temporary batches during chunked generation
- `user_progress` - User answer tracking
- `users` - User accounts with enrolled_courses

## API Endpoints

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check (includes DB status) |

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user info (requires auth) |

### Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/courses/validate` | Validate topic before generation |
| POST | `/api/v1/courses/generate` | Generate chapters from topic (requires auth) |
| GET | `/api/v1/courses/my-courses` | Get user's created courses (requires auth) |
| GET | `/api/v1/courses/{id}` | Get course by ID (requires auth) |
| DELETE | `/api/v1/courses/{id}` | Delete a course (requires auth) |
| GET | `/api/v1/courses/providers` | Get AI provider config |
| GET | `/api/v1/courses/config-presets` | Get difficulty presets |
| GET | `/api/v1/courses/supported-topics` | Get mock data topics |

### My Courses Endpoints (Enrolled)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/my-courses/` | Get enrolled courses (requires auth) |

### Question Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/questions/generate` | Generate MCQ and T/F questions for a chapter |
| POST | `/api/v1/questions/analyze-count` | Get recommended question count without generating |
| GET | `/api/v1/questions/sample` | Get sample questions (uses mock) |
| GET | `/api/v1/questions/config` | Get question generation configuration |

### Progress Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/progress/submit` | Submit answer and update progress |
| GET | `/api/v1/progress/` | Get user's progress (requires auth) |

## Course Generation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    POST /api/v1/courses/generate                    │
│                                                                     │
│  Request: { topic, difficulty, skip_validation? }                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Topic Validation (TopicValidator)                          │
│  ─────────────────────────────────────────                          │
│  • Quick validation: pattern matching for broad/vague topics        │
│  • AI validation: Claude Haiku analyzes complexity                  │
│                                                                     │
│  Outcomes:                                                          │
│  • "accepted" → continue with complexity score                      │
│  • "rejected" → 400 error with suggestions                          │
│  • "needs_clarification" → 422 error with suggestions               │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Course Configuration (CourseConfigurator)                  │
│  ────────────────────────────────────────────────                   │
│  • Uses complexity score (1-10) from validation                     │
│  • Combines with difficulty preset (beginner/intermediate/advanced) │
│  • Returns: recommended_chapters, time_per_chapter, chapter_depth   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Cache Check (MongoDB)                                      │
│  ─────────────────────────────                                      │
│  • Check if course exists for topic + difficulty                    │
│  • If cached → return immediately                                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Chapter Generation (AI Service)                            │
│  ──────────────────────────────────────                             │
│  • AI generates exactly N chapters based on config                  │
│  • Each chapter has: title, summary, key_concepts, time estimate    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Save to Cache & Return                                     │
│  ────────────────────────────────                                   │
│  • Save to MongoDB for future requests                              │
│  • Return enriched response with study time estimates               │
└─────────────────────────────────────────────────────────────────────┘
```

## Topic Validator

The `TopicValidator` ensures topics are appropriate for course generation.

### Quick Validation (No AI Cost)
- Rejects single-word broad topics: "Physics", "Math", "Business", etc.
- Rejects vague terms: "stuff", "things", "about", etc.
- Allows specific known courses: "Python", "Docker", "Calculus"

### AI Validation (Claude Haiku)
- Analyzes topic complexity (score 1-10)
- Determines if topic fits a single course
- Provides alternative suggestions if rejected

### Usage

```python
from app.services.topic_validator import get_topic_validator

validator = get_topic_validator()

# Quick check only (free)
result = validator.quick_validate("Physics")
# Returns: TopicValidationResult(status="rejected", reason="too_broad", ...)

# Full validation (quick + AI)
result = await validator.validate("Python Web Development")
# Returns: TopicValidationResult(status="accepted", complexity={score: 6, ...})
```

## Course Configurator

The `CourseConfigurator` determines optimal course structure.

### Difficulty Presets

| Difficulty | Chapters | Time/Chapter | Depth |
|------------|----------|--------------|-------|
| beginner | 4-6 | 25 min | overview |
| intermediate | 6-8 | 45 min | detailed |
| advanced | 8-12 | 90 min | comprehensive |

### Complexity Scaling
- Score 1-3: Use minimum chapters for difficulty
- Score 4-6: Use mid-range chapters
- Score 7-10: Use maximum chapters

### Usage

```python
from app.services.course_configurator import get_course_configurator

configurator = get_course_configurator()
config = configurator.get_config(complexity_score=7, difficulty="intermediate")
# Returns: CourseConfig(
#   recommended_chapters=7,
#   estimated_study_hours=5.25,
#   time_per_chapter_minutes=45,
#   chapter_depth="detailed",
#   difficulty="intermediate"
# )
```

## Question Generation

The question generation system creates MCQ and True/False questions for course chapters.

### Question Models

```python
from app.models.question import (
    QuestionType,        # Enum: MCQ, TRUE_FALSE
    QuestionDifficulty,  # Enum: EASY, MEDIUM, HARD
    MCQQuestion,         # Multiple choice question
    TrueFalseQuestion,   # True/False question
    ChapterQuestions,    # Collection with computed totals
    QuestionGenerationConfig,  # Generation configuration
)
```

### MCQQuestion

```python
MCQQuestion(
    id="uuid",                    # Auto-generated UUID
    type=QuestionType.MCQ,
    difficulty=QuestionDifficulty.MEDIUM,
    question_text="What is...?",
    options=["A) ...", "B) ...", "C) ...", "D) ..."],
    correct_answer="A",           # Pattern: ^[A-D]$
    explanation="A is correct because...",
    points=1
)
```

### TrueFalseQuestion

```python
TrueFalseQuestion(
    id="uuid",
    type=QuestionType.TRUE_FALSE,
    difficulty=QuestionDifficulty.EASY,
    question_text="Python is a programming language.",
    correct_answer=True,
    explanation="True because...",
    points=1
)
```

### Question Generation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   POST /api/v1/questions/generate                   │
│                                                                     │
│  Request: { topic, difficulty, chapter_number, chapter_title,       │
│             key_concepts, override_mcq_count?, override_tf_count? } │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Question Count Analysis (QuestionAnalyzer)                 │
│  ───────────────────────────────────────────────────                │
│  • Uses Haiku 3.5 for cost-efficient analysis                       │
│  • Analyzes topic complexity and key concepts                       │
│  • Returns recommended MCQ and T/F counts                           │
│  • Caches results for same chapter content                          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Build Configuration                                        │
│  ────────────────────────────                                       │
│  • Derive audience from difficulty:                                 │
│    - beginner → "teenagers, simple language"                        │
│    - intermediate → "college students, technical terms"             │
│    - advanced → "professionals, industry jargon"                    │
│  • Apply overrides if provided                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Generate Questions (QuestionGenerator)                     │
│  ───────────────────────────────────────────────                    │
│  • Builds optimized prompt with rules:                              │
│    - Cover all key concepts                                         │
│    - Mix of easy/medium/hard (30/50/20%)                           │
│    - No trick questions or "all of above"                          │
│    - Include explanations                                           │
│  • Parses AI response and validates                                 │
│  • Retries once on JSON parse failure                               │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Return ChapterQuestions                                    │
│  ────────────────────────────────                                   │
│  • Assigns UUIDs to each question                                   │
│  • Computes total_questions and total_points                        │
│  • Includes generation_info (model, timing, reasoning)              │
└─────────────────────────────────────────────────────────────────────┘
```

### Default Question Counts

| Difficulty | MCQ | True/False | Total |
|------------|-----|------------|-------|
| beginner | 8 | 5 | 13 |
| intermediate | 12 | 6 | 18 |
| advanced | 20 | 8 | 28 |

### Services

#### QuestionAnalyzer

Determines optimal question count using AI:

```python
from app.services.question_analyzer import get_question_analyzer

analyzer = get_question_analyzer()
recommendation = await analyzer.analyze_chapter(
    chapter=chapter,
    topic="AWS Solutions Architect",
    difficulty="advanced"
)
# Returns: QuestionCountRecommendation(
#   mcq_count=20,
#   true_false_count=8,
#   total_count=28,
#   reasoning="Professional certification topic..."
# )
```

#### QuestionGenerator

Orchestrates question generation:

```python
from app.services.question_generator import get_question_generator

generator = get_question_generator()
chapter_questions = await generator.generate_questions(config)
# Returns: ChapterQuestions with MCQ and T/F questions
```

## Example API Requests

### Validate Topic Only

```bash
# Check if topic is valid before generating
curl -X POST "http://localhost:8000/api/v1/courses/validate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python Web Development with FastAPI"}'

# Response (accepted):
{
  "status": "accepted",
  "topic": "Python Web Development with FastAPI",
  "normalized_topic": "python web development with fastapi",
  "reason": null,
  "message": "This is a well-scoped topic suitable for a single course.",
  "suggestions": [],
  "complexity": {
    "score": 6,
    "level": "intermediate",
    "estimated_chapters": 6,
    "estimated_hours": 15.0,
    "reasoning": "Covers web framework concepts with practical depth"
  }
}

# Response (rejected):
curl -X POST "http://localhost:8000/api/v1/courses/validate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Physics"}'

{
  "status": "rejected",
  "topic": "Physics",
  "reason": "too_broad",
  "message": "'Physics' is too broad for a single course.",
  "suggestions": [
    "Classical Mechanics for Engineers",
    "Introduction to Quantum Physics",
    "Thermodynamics Fundamentals"
  ]
}
```

### Generate Course with Difficulty

```bash
# Beginner course (4-6 chapters, 25 min each, overview depth)
curl -X POST "http://localhost:8000/api/v1/courses/generate?provider=mock" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Project Management", "difficulty": "beginner"}'

# Intermediate course (6-8 chapters, 45 min each, detailed depth)
curl -X POST "http://localhost:8000/api/v1/courses/generate?provider=mock" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python Programming", "difficulty": "intermediate"}'

# Advanced course (8-12 chapters, 90 min each, comprehensive depth)
curl -X POST "http://localhost:8000/api/v1/courses/generate?provider=claude" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Machine Learning Fundamentals", "difficulty": "advanced"}'

# Skip validation (for testing)
curl -X POST "http://localhost:8000/api/v1/courses/generate?provider=mock" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Any Topic", "difficulty": "beginner", "skip_validation": true}'
```

### Response Format

```json
{
  "topic": "Python Programming",
  "difficulty": "intermediate",
  "total_chapters": 6,
  "estimated_study_hours": 4.5,
  "time_per_chapter_minutes": 45,
  "complexity_score": 5,
  "message": "Generated 6 intermediate-level chapters using mock",
  "config": {
    "recommended_chapters": 6,
    "estimated_study_hours": 4.5,
    "time_per_chapter_minutes": 45,
    "chapter_depth": "detailed",
    "difficulty": "intermediate"
  },
  "chapters": [
    {
      "number": 1,
      "title": "Python Basics",
      "summary": "Learn the fundamentals of Python programming...",
      "key_concepts": ["Syntax", "Variables", "Data types"],
      "difficulty": "intermediate",
      "estimated_time_minutes": 45
    }
  ]
}
```

### Analyze Question Count

```bash
# Get recommended question count without generating
curl -X POST "http://localhost:8000/api/v1/questions/analyze-count" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AWS Solutions Architect",
    "difficulty": "advanced",
    "chapter_number": 1,
    "chapter_title": "EC2 and Compute",
    "chapter_summary": "Learn about EC2 instances and compute services.",
    "key_concepts": ["EC2", "Auto Scaling", "Load Balancers", "EBS"],
    "estimated_time_minutes": 90
  }'

# Response:
{
  "mcq_count": 20,
  "true_false_count": 8,
  "total_count": 28,
  "reasoning": "Professional certification topic with 4 key concepts requiring comprehensive coverage."
}
```

### Generate Questions

```bash
# Generate questions for a beginner chapter
curl -X POST "http://localhost:8000/api/v1/questions/generate?provider=mock" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Basics",
    "difficulty": "beginner",
    "chapter_number": 1,
    "chapter_title": "Variables and Data Types",
    "key_concepts": ["variables", "strings", "integers", "floats"]
  }'

# Generate questions for an advanced chapter
curl -X POST "http://localhost:8000/api/v1/questions/generate?provider=claude" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AWS Solutions Architect",
    "difficulty": "advanced",
    "chapter_number": 3,
    "chapter_title": "High Availability Architecture",
    "key_concepts": ["Multi-AZ", "Auto Scaling", "Load Balancing", "Disaster Recovery"],
    "override_mcq_count": 25,
    "override_tf_count": 10
  }'

# Response:
{
  "chapter_number": 1,
  "chapter_title": "Variables and Data Types",
  "total_questions": 13,
  "total_points": 13,
  "mcq_questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "mcq",
      "difficulty": "easy",
      "question_text": "What is a variable in Python?",
      "options": [
        "A) A container that stores data values",
        "B) A type of loop",
        "C) A function definition",
        "D) A comment in code"
      ],
      "correct_answer": "A",
      "explanation": "A variable is a named container that stores data values in memory.",
      "points": 1
    }
  ],
  "true_false_questions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "type": "true_false",
      "difficulty": "easy",
      "question_text": "In Python, variable names are case-sensitive.",
      "correct_answer": true,
      "explanation": "True. Python treats 'myVar' and 'myvar' as different variables.",
      "points": 1
    }
  ],
  "generation_info": {
    "model": "claude-3-5-haiku-20241022",
    "audience": "beginners, kids, or teens with no prior knowledge",
    "provider": "mock",
    "recommended_mcq": 8,
    "recommended_tf": 5,
    "actual_mcq": 8,
    "actual_tf": 5,
    "generation_time_ms": 150
  }
}
```

### Get Sample Questions

```bash
# Get sample questions for UI testing
curl "http://localhost:8000/api/v1/questions/sample?topic=Python&difficulty=intermediate&mcq_count=5&tf_count=3"
```

### Get Question Config

```bash
# Get current question generation configuration
curl "http://localhost:8000/api/v1/questions/config"

# Response:
{
  "model": "claude-3-5-haiku-20241022",
  "model_analysis": "claude-3-5-haiku-20241022",
  "max_tokens": 2000,
  "default_counts": {
    "beginner": {"mcq": 8, "tf": 5},
    "intermediate": {"mcq": 12, "tf": 6},
    "advanced": {"mcq": 20, "tf": 8}
  },
  "audience_mapping": {
    "beginner": "teenagers and beginners; simple language",
    "intermediate": "college students and professionals; technical terms allowed",
    "advanced": "experienced professionals; industry jargon acceptable"
  }
}
```

## Architecture

### AI Service Pattern

All AI providers implement `BaseAIService` (abstract base class):

```python
class BaseAIService(ABC):
    @abstractmethod
    async def generate_chapters(self, topic: str, config: CourseConfig, content: str = "") -> List[Chapter]

    @abstractmethod
    async def generate_questions(self, chapter: Chapter, num_mcq=5, num_tf=3) -> Dict

    @abstractmethod
    async def generate_feedback(self, user_progress: Dict, weak_areas: List) -> str

    @abstractmethod
    async def check_answer(self, question: str, user_answer: str, correct_answer: str) -> Dict

    @abstractmethod
    async def answer_question(self, question: str, context: str) -> str
```

### Factory Pattern

```python
from app.services.ai_service_factory import AIServiceFactory
from app.config import UseCase

# Get service based on config
service = AIServiceFactory.get_service(UseCase.CHAPTER_GENERATION)

# Override provider
service = AIServiceFactory.get_service(UseCase.CHAPTER_GENERATION, provider_override="mock")
```

### Use Cases (from config.py)

- `UseCase.CHAPTER_GENERATION` - Breaking content into chapters
- `UseCase.QUESTION_GENERATION` - Creating quiz questions (Haiku)
- `UseCase.QUESTION_COUNT_ANALYSIS` - Analyzing optimal question counts (Haiku)
- `UseCase.STUDENT_FEEDBACK` - Personalized feedback
- `UseCase.ANSWER_CHECKING` - Evaluating answers
- `UseCase.RAG_QUERY` - Answering student questions
- `UseCase.TOPIC_VALIDATION` - Validating topics (Haiku)

## Configuration

Environment variables in `.env`:

```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...  # Optional
GOOGLE_API_KEY=...     # Optional, for Gemini

# Provider selection: mock | claude | openai | gemini
DEFAULT_AI_PROVIDER=mock

# Models per use case (claude-*, gpt-*, gemini-*)
MODEL_CHAPTER_GENERATION=mock           # or claude-sonnet-4-20250514 or gemini-1.5-pro
MODEL_QUESTION_GENERATION=mock          # or claude-3-5-haiku-20241022 or gemini-1.5-flash
MODEL_QUESTION_COUNT_ANALYSIS=mock      # or claude-3-5-haiku-20241022 or gemini-1.5-flash
MODEL_STUDENT_FEEDBACK=mock             # or claude-sonnet-4-20250514 or gemini-1.5-pro
MODEL_ANSWER_CHECKING=mock              # or claude-haiku-4-5-20251001 or gemini-1.5-flash
MODEL_RAG_QUERY=mock                    # or claude-haiku-4-5-20251001 or gemini-1.5-flash
MODEL_TOPIC_VALIDATION=mock             # or claude-haiku-3-5-20241022 or gemini-1.5-flash

# Token Limits
MAX_TOKENS_CHAPTER=4000
MAX_TOKENS_QUESTION=2000
MAX_TOKENS_QUESTION_COUNT=300
MAX_TOKENS_VALIDATION=500

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_learning_platform
```

## Current Status

### Completed
- FastAPI application setup
- Pydantic models for Course, Chapter, Questions, Validation
- Abstract AI service interface (BaseAIService)
- AI Service Factory with provider routing
- Mock AI service (difficulty-aware with question templates)
- Claude AI service implementation (chapters + questions)
- OpenAI AI service implementation (chapters + questions)
- Gemini AI service implementation (chapters + questions)
- Topic Validator with quick + AI validation
- Course Configurator with difficulty presets
- MongoDB integration with caching
- POST /api/v1/courses/generate endpoint
- POST /api/v1/courses/validate endpoint
- GET /api/v1/courses/config-presets endpoint
- Per-use-case model configuration
- Runtime provider override via query parameter
- **Question Generation System:**
  - Pydantic models (MCQQuestion, TrueFalseQuestion, ChapterQuestions)
  - QuestionAnalyzer service (AI-based count recommendations)
  - QuestionGenerator service (question generation orchestration)
  - POST /api/v1/questions/generate endpoint
  - POST /api/v1/questions/analyze-count endpoint
  - GET /api/v1/questions/sample endpoint
  - GET /api/v1/questions/config endpoint
  - Difficulty-aware audience targeting
  - Caching for question count analysis
- Comprehensive test suite (courses + questions)

### Recently Completed
- **User Authentication** - JWT auth with bcrypt password hashing
- **Progress Tracking** - Track user answers and scores
- **User Courses** - Save/list/delete user's courses with ownership
- **Course Enrollment** - Auto-enroll users on course generation

## User Courses

Courses are now linked to users and persist across sessions.

### Database Model

**CourseDocument** (MongoDB `courses` collection):
```python
{
    "_id": ObjectId,
    "user_id": str,              # User who created the course
    "topic": str,                # Normalized topic (lowercase)
    "original_topic": str,       # Original topic as entered
    "difficulty": str,           # beginner/intermediate/advanced
    "complexity_score": int,     # 1-10 (from validation)
    "total_chapters": int,
    "chapters": [                # Array of Chapter objects
        {
            "number": int,
            "title": str,
            "summary": str,
            "key_concepts": [str],
            "difficulty": str,
            "estimated_time_minutes": int
        }
    ],
    "provider": str,             # AI provider used (claude/openai/mock)
    "created_at": datetime,
    "updated_at": datetime
}
```

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/courses/generate` | Yes | Create new course (auto-enrolls user) |
| GET | `/api/v1/courses/my-courses` | Yes | Get user's created courses |
| GET | `/api/v1/courses/{id}` | Yes | Get course details (owner only) |
| DELETE | `/api/v1/courses/{id}` | Yes | Delete course (owner only) |

### Frontend Integration

**Routes:**
- `/app/my-courses` - Grid of user's course cards (dashboard)
- `/app/course` - Course detail view
- `/app` or `/app/new` - Create new course

**Flow:**
1. User logs in → redirected to `/app/my-courses`
2. User clicks "New Course" → `/app/new`
3. Course generated → success message → redirect to `/app/my-courses`
4. User clicks course card → navigate to course details

**CourseCard Component** (`frontend/src/components/CourseCard.jsx`):
- Topic title
- Difficulty badge (color-coded: green/yellow/red)
- Complexity score (X/10)
- Chapter count
- Quiz ready indicator
- Relative date (Today, Yesterday, X days ago)
- Delete button with confirmation

### TODO
1. **PDF Upload** - Extract text from PDFs, generate chapters
2. **AI Mentor Feedback** - Personalized study recommendations
3. **RAG System** - Vector embeddings for document Q&A
4. **Chapter Verification** - Double-check generated chapters with secondary LLM to ensure completeness

## Code Style

- Use async/await for all I/O operations
- Use Pydantic models for request/response validation
- Follow FastAPI dependency injection patterns
- Use type hints everywhere
- Services go in `app/services/`
- API routes go in `app/routers/`
- Database operations go in `app/db/`

## AI Provider Rules (IMPORTANT)

**All new AI features MUST be LLM-agnostic and support mock provider:**

1. **Use `AIServiceFactory`** - Never instantiate AI clients directly (no `AsyncAnthropic()`, `AsyncOpenAI()`, etc.)
   ```python
   # WRONG
   self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

   # CORRECT
   ai_service = AIServiceFactory.get_service(UseCase.YOUR_USE_CASE)
   ```

2. **Implement in `BaseAIService`** - Add new AI methods to the abstract base class first
   ```python
   # In base_ai_service.py
   @abstractmethod
   async def your_new_method(self, ...) -> YourReturnType:
       pass
   ```

3. **Implement in ALL providers** - Claude, OpenAI, Gemini, AND Mock
   - Mock implementation enables testing without API costs
   - All providers must return the same response structure

4. **Use `UseCase` enum** - Add new use cases to `config.py` for per-operation model selection
   ```python
   class UseCase(str, Enum):
       YOUR_NEW_FEATURE = "your_new_feature"
   ```

5. **Support provider override** - API endpoints should accept `?provider=` query parameter

**Why?** This ensures:
- Easy A/B testing between providers
- Cost optimization (use cheaper models where appropriate)
- Testing without API costs (mock)
- Future-proof for new providers

## Key Files to Understand

1. `app/config.py` - All settings, AI model configuration
2. `app/services/base_ai_service.py` - Interface all providers implement
3. `app/services/topic_validator.py` - Topic validation logic
4. `app/services/course_configurator.py` - Course structure configuration
5. `app/services/question_analyzer.py` - AI-based question count analysis
6. `app/services/question_generator.py` - Question generation orchestration
7. `app/services/auth_service.py` - JWT tokens and password hashing
8. `app/routers/courses.py` - Course API endpoints
9. `app/routers/questions.py` - Question API endpoints
10. `app/routers/auth.py` - Authentication endpoints
11. `app/models/course.py` - Course and Chapter models
12. `app/models/question.py` - Question models (MCQ, T/F, ChapterQuestions)
13. `app/models/user.py` - User models
14. `app/models/validation.py` - Validation result models
15. `app/dependencies/auth.py` - Authentication dependency
16. `app/db/user_repository.py` - User database operations

## Adding a New AI Provider

1. Create `app/services/new_provider_service.py`
2. Extend `BaseAIService`
3. Implement all abstract methods
4. Add to factory in `ai_service_factory.py`
5. Update config.py if needed

## Testing

```bash
# Run server first
python run.py

# In another terminal, run test suite
python test_api.py

# Or test individual endpoints with curl
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/courses/providers
curl http://localhost:8000/api/v1/courses/config-presets
```

## Common Issues

**ModuleNotFoundError: No module named 'app'**
→ Run from project root: `cd D:\Projects\be-ready && python run.py`

**ValidationError: Extra inputs are not permitted**
→ Update `.env` file - old variable names don't match new config.py

**OpenAI/Claude API errors**
→ Check API key in `.env`, ensure provider is set correctly

**Topic rejected unexpectedly**
→ Use `skip_validation: true` for testing, or provide more specific topic

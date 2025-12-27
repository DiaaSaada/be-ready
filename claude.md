# CLAUDE.md - AI Learning Platform

## Project Overview

An AI-powered learning platform backend built with FastAPI. The system takes topics or PDF materials, validates them, breaks them into chapters using AI (Claude/OpenAI), generates quiz questions, tracks user progress, and provides personalized mentoring feedback.

## Tech Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: MongoDB with Motor (async driver)
- **AI Providers**: Anthropic Claude, OpenAI GPT, Mock (for testing)
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
│   │   └── validation.py          # TopicValidationResult, TopicComplexity
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_ai_service.py     # Abstract base class (interface)
│   │   ├── ai_service_factory.py  # Factory pattern for provider selection
│   │   ├── mock_ai_service.py     # Mock implementation
│   │   ├── claude_ai_service.py   # Anthropic Claude implementation
│   │   ├── openai_ai_service.py   # OpenAI GPT implementation
│   │   ├── topic_validator.py     # Topic validation service
│   │   ├── course_configurator.py # Course structure configuration
│   │   ├── question_analyzer.py   # AI-based question count analysis
│   │   └── question_generator.py  # Question generation orchestrator
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── courses.py             # Course generation endpoints
│   │   └── questions.py           # Question generation endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py          # MongoDB connection management
│   │   ├── models.py              # Document models
│   │   └── crud.py                # Database operations
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
- `courses` - Cached generated courses (by topic + difficulty)
- `questions` - Cached generated questions (by topic + difficulty + chapter)
- `question_batches` - Temporary batches during chunked generation
- `user_progress` - User answer tracking

## API Endpoints

### Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check (includes DB status) |
| POST | `/api/v1/courses/validate` | Validate topic before generation |
| POST | `/api/v1/courses/generate` | Generate chapters from topic |
| GET | `/api/v1/courses/providers` | Get AI provider config |
| GET | `/api/v1/courses/config-presets` | Get difficulty presets |
| GET | `/api/v1/courses/supported-topics` | Get mock data topics |

### Question Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/questions/generate` | Generate MCQ and T/F questions for a chapter |
| POST | `/api/v1/questions/analyze-count` | Get recommended question count without generating |
| GET | `/api/v1/questions/sample` | Get sample questions (uses mock) |
| GET | `/api/v1/questions/config` | Get question generation configuration |

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

# Provider selection: mock | claude | openai
DEFAULT_AI_PROVIDER=mock

# Models per use case
MODEL_CHAPTER_GENERATION=mock           # or claude-sonnet-4-20250514
MODEL_QUESTION_GENERATION=mock          # or claude-3-5-haiku-20241022
MODEL_QUESTION_COUNT_ANALYSIS=mock      # or claude-3-5-haiku-20241022
MODEL_STUDENT_FEEDBACK=mock             # or claude-sonnet-4-20250514
MODEL_ANSWER_CHECKING=mock              # or claude-haiku-4-5-20251001
MODEL_RAG_QUERY=mock                    # or claude-haiku-4-5-20251001
MODEL_TOPIC_VALIDATION=mock             # or claude-haiku-3-5-20241022

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

### TODO
1. **PDF Upload** - Extract text from PDFs, generate chapters
2. **Progress Tracking** - Track user answers and scores
3. **AI Mentor Feedback** - Personalized study recommendations
4. **RAG System** - Vector embeddings for document Q&A
5. **User Authentication** - JWT or session-based auth
6. **Frontend** - React/Vue UI

## Code Style

- Use async/await for all I/O operations
- Use Pydantic models for request/response validation
- Follow FastAPI dependency injection patterns
- Use type hints everywhere
- Services go in `app/services/`
- API routes go in `app/routers/`
- Database operations go in `app/db/`

## Key Files to Understand

1. `app/config.py` - All settings, AI model configuration
2. `app/services/base_ai_service.py` - Interface all providers implement
3. `app/services/topic_validator.py` - Topic validation logic
4. `app/services/course_configurator.py` - Course structure configuration
5. `app/services/question_analyzer.py` - AI-based question count analysis
6. `app/services/question_generator.py` - Question generation orchestration
7. `app/routers/courses.py` - Course API endpoints
8. `app/routers/questions.py` - Question API endpoints
9. `app/models/course.py` - Course and Chapter models
10. `app/models/question.py` - Question models (MCQ, T/F, ChapterQuestions)
11. `app/models/validation.py` - Validation result models

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

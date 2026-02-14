# AI Mentor Feedback Feature - Implementation Plan

## Overview

Implement AI Mentor Feedback that triggers after completing N chapters, analyzes quiz results to find weak areas, and generates a Gap Covering Quiz.

**Key Decisions:**
- Weak Area Detection: Hybrid (chapter scores + wrong answer analysis)
- Trigger: Backend provides `mentor_available` flag
- Hints: Optional toggle (user chooses to show/hide)
- Scope: Backend only
- **Course Slug**: Courses identified by unique slug (e.g., `python-programming-beginner-a7x3k2`)
- **Gap Quiz Strategy**:
  - **Always free**: Wrong answers from completed quizzes (pulled from user_progress)
  - **Optional AI**: User can request extra AI-generated questions on weak areas

---

## Step 1: Add Course Slug

**Files to Modify:**
- `backend/app/models/course.py`
- `backend/app/db/models.py`
- `backend/app/routers/courses.py`

**Changes:**

1. Add slug generation utility:
   ```python
   import secrets
   import re

   def generate_course_slug(topic: str, difficulty: str) -> str:
       """Generate slug like 'python-programming-beginner-a7x3k2'"""
       # Normalize topic: lowercase, replace spaces with hyphens
       base = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
       # Truncate to reasonable length
       base = base[:40]
       # Add difficulty and random suffix
       suffix = secrets.token_hex(3)  # 6 alphanumeric chars
       return f"{base}-{difficulty}-{suffix}"
   ```

2. Add `slug` field to Course model:
   ```python
   class Course(BaseModel):
       slug: str  # Unique identifier like "python-programming-beginner-a7x3k2"
       topic: str
       # ... existing fields
   ```

3. Update CourseDocument in db/models.py:
   ```python
   class CourseDocument(BaseModel):
       slug: str = Field(default_factory=lambda: "")  # Generated on create
       # ... existing fields
   ```

4. Update course generation to create slug:
   - In `POST /api/v1/courses/generate`, generate slug before saving
   - Add unique index on `slug` field in MongoDB

5. Add endpoint to get course by slug:
   ```python
   @router.get("/{slug}")
   async def get_course_by_slug(slug: str) -> Course:
       """Get course by unique slug"""
   ```

**Test:** New courses have slugs, existing endpoint works

---

## Step 2: Add Mentor Configuration Settings

**Files to Modify:**
- `backend/app/config.py`

**Changes:**
1. Add settings to `Settings` class:
   ```python
   mentor_chapters_threshold: int = 3
   mentor_weak_score_threshold: float = 0.7
   model_gap_quiz: str = "claude-3-5-haiku-20241022"
   max_tokens_gap_quiz: int = 4000
   ```

2. Add to `UseCase` enum:
   ```python
   GAP_QUIZ_GENERATION = "gap_quiz_generation"
   ```

3. Update `get_model_for_use_case()` and `get_max_tokens_for_use_case()`

**Test:** App starts, settings load from `.env`

---

## Step 3: Create Mentor Data Models

**Files to Create:**
- `backend/app/models/mentor.py`

**Models:**
```python
class WeakConcept(BaseModel):
    chapter_number: int
    chapter_title: str
    concept: str
    wrong_count: int
    total_questions: int
    sample_wrong_questions: List[str]

class WeakArea(BaseModel):
    chapter_number: int
    chapter_title: str
    score: float
    weak_concepts: List[WeakConcept]

class MentorAnalysis(BaseModel):
    user_id: str
    course_slug: str  # Reference by slug
    total_chapters_completed: int
    average_score: float
    weak_areas: List[WeakArea]
    mentor_available: bool

class GapQuizQuestion(BaseModel):
    id: str
    type: Literal["mcq", "true_false"]
    difficulty: QuestionDifficulty
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: Union[str, bool]
    explanation: str
    hint: Optional[str] = None
    source_chapter: int
    source_concept: str

class WrongAnswer(BaseModel):
    """A question the user got wrong - pulled from user_progress"""
    question_id: str
    question_text: str
    question_type: Literal["mcq", "true_false"]
    user_answer: str
    correct_answer: Union[str, bool]
    explanation: str
    chapter_number: int
    chapter_title: str
    hint: Optional[str] = None  # Added if include_hints=True

class GapQuiz(BaseModel):
    """Gap quiz combining wrong answers + optional AI questions"""
    course_slug: str
    wrong_answers: List[WrongAnswer]  # Always included (free)
    extra_questions: List[GapQuizQuestion]  # Only if generate_extra=True
    total_questions: int
    wrong_answers_count: int
    extra_questions_count: int
    include_hints: bool

class MentorStatusResponse(BaseModel):
    mentor_available: bool
    chapters_completed: int
    chapters_required: int
    average_score: float
    weak_areas_count: int
    wrong_answers_count: int  # How many wrong answers available
    course_slug: str

class GenerateGapQuizRequest(BaseModel):
    course_slug: str
    include_hints: bool = False
    generate_extra: bool = False  # Opt-in for AI-generated questions
    extra_questions_count: int = 5  # How many AI questions to add (if generate_extra=True)

class MentorFeedbackResponse(BaseModel):
    analysis: MentorAnalysis
    feedback: str
    quiz: GapQuiz
    ai_generated: bool  # True if extra questions were AI-generated
```

**Test:** Models import without errors

---

## Step 4: Add Wrong Answers Query to CRUD

**Files to Modify:**
- `backend/app/db/crud.py`

**Add CRUD operations:**
```python
async def get_wrong_answers_for_course(
    user_id: str,
    course_topic: str,
    difficulty: str
) -> List[Dict]:
    """
    Get all wrong answers for a user across all chapters of a course.

    Queries user_progress collection, filters answers where is_correct=False.
    Returns list of wrong answer records with chapter info.
    """
    db = MongoDB.get_db()

    # Find all progress records for this user/course
    cursor = db["user_progress"].find({
        "user_id": user_id,
        "course_topic": course_topic.lower(),
        "difficulty": difficulty
    })

    wrong_answers = []
    async for record in cursor:
        chapter_num = record.get("chapter_number")
        chapter_title = record.get("chapter_title", "")

        for answer in record.get("answers", []):
            if not answer.get("is_correct", True):
                wrong_answers.append({
                    "question_id": answer.get("question_id"),
                    "question_text": answer.get("question_text"),
                    "user_answer": answer.get("selected"),
                    "correct_answer": answer.get("correct"),
                    "chapter_number": chapter_num,
                    "chapter_title": chapter_title
                })

    return wrong_answers
```

**Note:** No new MongoDB collection needed. Wrong answers come from existing `user_progress` collection. AI-generated extra questions are returned directly without caching (user pays for each generation).

**Test:** Query returns wrong answers correctly

---

## Step 5: Create Weak Area Analyzer Service

**Files to Create:**
- `backend/app/services/weak_area_analyzer.py`

**Key Methods:**
```python
class WeakAreaAnalyzer:
    async def analyze_user_progress(
        self, user_id: str, course_slug: str
    ) -> MentorAnalysis:
        """
        1. Get course by slug to find topic/difficulty
        2. Fetch all progress records for user/course
        3. Filter chapters with score < threshold (0.7)
        4. Collect all wrong answers
        5. Return MentorAnalysis with weak_areas and wrong_answers_count
        """

    def _identify_weak_chapters(self, progress_records: List[Dict]) -> List[Dict]:
        """Find chapters with score < mentor_weak_score_threshold"""

    async def get_wrong_answers(
        self, user_id: str, course_slug: str
    ) -> List[WrongAnswer]:
        """
        Get all wrong answers for gap quiz.

        1. Get course by slug
        2. Query user_progress for wrong answers
        3. Fetch original questions to get explanations
        4. Return formatted WrongAnswer objects
        """

    def is_mentor_available(self, chapters_completed: int) -> bool:
        """Check if chapters_completed >= threshold"""

def get_weak_area_analyzer() -> WeakAreaAnalyzer:
    """Singleton factory"""
```

**Test:** Analyzer returns valid MentorAnalysis and wrong answers

---

## Step 6: Add Extra Questions Generation to AI Services (Optional Feature)

**Note:** This step is only needed when `generate_extra=True`. The base gap quiz (wrong answers) requires no AI.

**Files to Modify:**
- `backend/app/services/base_ai_service.py` - Add abstract method
- `backend/app/services/mock_ai_service.py` - Implement
- `backend/app/services/claude_ai_service.py` - Implement
- `backend/app/services/openai_ai_service.py` - Implement
- `backend/app/services/gemini_ai_service.py` - Implement

**Add to BaseAIService:**
```python
@abstractmethod
async def generate_extra_gap_questions(
    self,
    weak_areas: List[WeakArea],
    wrong_answers: List[WrongAnswer],  # Context: what user got wrong
    course_topic: str,
    difficulty: str,
    num_questions: int = 5,
    include_hints: bool = False,
    user_id: Optional[str] = None,
    context: Optional[str] = None
) -> List[GapQuizQuestion]:
    """
    Generate ADDITIONAL questions on weak areas.

    Uses wrong_answers as context to avoid duplicates and
    focus on reinforcing the same concepts user struggled with.
    """
    pass
```

**Claude/OpenAI/Gemini Prompt:**
```
The user struggled with these questions:
{wrong_answers_summary}

Generate {num_questions} NEW questions to reinforce these weak areas:
{weak_areas_json}

Requirements:
- Focus on the same concepts the user got wrong
- Do NOT repeat the exact same questions
- Mix MCQ and True/False types
- Provide clear explanations
{if include_hints: "- Include a helpful hint for each question"}

Return JSON: { "questions": [...] }
```

**Test:** `generate_extra=true&provider=mock` returns extra questions

---

## Step 7: Add Token Usage Operation Type

**Files to Modify:**
- `backend/app/models/token_usage.py`

**Change:**
```python
class OperationType(str, Enum):
    # ... existing
    GAP_QUIZ_GENERATION = "GAP_QUIZ_GENERATION"
```

**Test:** Token usage logged for gap quiz generation

---

## Step 8: Create Mentor Router

**Files to Create:**
- `backend/app/routers/mentor.py`

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/mentor/{course_slug}/status` | Check if mentor available |
| GET | `/api/v1/mentor/{course_slug}/analysis` | Get detailed weak area analysis |
| POST | `/api/v1/mentor/{course_slug}/generate-quiz` | Generate gap covering quiz |
| GET | `/api/v1/mentor/config` | Get mentor configuration |

```python
@router.get("/{course_slug}/status")
async def get_mentor_status(
    course_slug: str,
    current_user = Depends(get_current_user)
) -> MentorStatusResponse:
    """Returns mentor_available flag for frontend"""

@router.get("/{course_slug}/analysis")
async def get_mentor_analysis(
    course_slug: str,
    current_user = Depends(get_current_user)
) -> MentorAnalysis:
    """Returns detailed weak areas analysis for this user"""

@router.post("/{course_slug}/generate-quiz")
async def generate_gap_quiz(
    course_slug: str,
    request: GenerateGapQuizRequest,
    provider: Optional[str] = None,
    current_user = Depends(get_current_user)
) -> MentorFeedbackResponse:
    """
    1. Get weak area analysis for user
    2. Check cache for existing gap quiz (user-agnostic)
    3. If cached, return it with cached=True
    4. If not, generate via AI and save to cache
    5. Generate personalized feedback
    6. Return combined response
    """

@router.get("/config")
async def get_mentor_config():
    """Return current mentor settings"""
```

**Logic in generate_gap_quiz:**
```python
# 1. Get weak area analysis
analysis = await analyzer.analyze_user_progress(user_id, course_slug)

# 2. Get wrong answers (always free)
wrong_answers = await analyzer.get_wrong_answers(user_id, course_slug)

# 3. Optionally add hints to wrong answers
if request.include_hints:
    wrong_answers = add_hints_to_questions(wrong_answers)

# 4. Optionally generate extra AI questions
extra_questions = []
if request.generate_extra and request.extra_questions_count > 0:
    ai_service = AIServiceFactory.get_service(UseCase.GAP_QUIZ_GENERATION)
    extra_questions = await ai_service.generate_extra_gap_questions(
        weak_areas=analysis.weak_areas,
        wrong_answers=wrong_answers,
        course_topic=course.topic,
        difficulty=course.difficulty,
        num_questions=request.extra_questions_count,
        include_hints=request.include_hints
    )

# 5. Build quiz
quiz = GapQuiz(
    course_slug=course_slug,
    wrong_answers=wrong_answers,
    extra_questions=extra_questions,
    total_questions=len(wrong_answers) + len(extra_questions),
    wrong_answers_count=len(wrong_answers),
    extra_questions_count=len(extra_questions),
    include_hints=request.include_hints
)

# 6. Generate personalized feedback
feedback = await ai_service.generate_feedback(...)

return MentorFeedbackResponse(
    analysis=analysis,
    feedback=feedback,
    quiz=quiz,
    ai_generated=len(extra_questions) > 0
)
```

**Test:** All endpoints respond correctly

---

## Step 9: Register Mentor Router

**Files to Modify:**
- `backend/app/main.py`

**Changes:**
```python
from app.routers import mentor

app.include_router(
    mentor.router,
    prefix="/api/v1/mentor",
    tags=["mentor"]
)
```

**Test:** `/docs` shows mentor endpoints, API calls work

---

## Step 10: Update .env.example

**Files to Modify:**
- `backend/.env.example`

**Add:**
```env
# Mentor Configuration
MENTOR_CHAPTERS_THRESHOLD=3
MENTOR_WEAK_SCORE_THRESHOLD=0.7
MODEL_GAP_QUIZ=claude-3-5-haiku-20241022
MAX_TOKENS_GAP_QUIZ=4000
```

**Test:** New users know available config options

---

## Files Summary

### New Files:
| File | Purpose |
|------|---------|
| `app/models/mentor.py` | Mentor Pydantic models |
| `app/services/weak_area_analyzer.py` | Weak area detection + wrong answers collection |
| `app/routers/mentor.py` | Mentor API endpoints |

### Modified Files:
| File | Changes |
|------|---------|
| `app/models/course.py` | Add slug field, slug generator (DONE) |
| `app/db/models.py` | Add slug to CourseDocument (DONE) |
| `app/db/crud.py` | Add `get_wrong_answers_for_course()`, slug functions (DONE) |
| `app/routers/courses.py` | Generate slug on create, add get by slug (DONE) |
| `app/config.py` | Add mentor settings, UseCase (DONE) |
| `app/services/base_ai_service.py` | Add `generate_extra_gap_questions()` abstract |
| `app/services/mock_ai_service.py` | Implement `generate_extra_gap_questions()` |
| `app/services/claude_ai_service.py` | Implement `generate_extra_gap_questions()` |
| `app/services/openai_ai_service.py` | Implement `generate_extra_gap_questions()` |
| `app/services/gemini_ai_service.py` | Implement `generate_extra_gap_questions()` |
| `app/models/token_usage.py` | Add GAP_QUIZ_GENERATION |
| `app/main.py` | Register mentor router |
| `.env.example` | Document new settings |

---

## API Flow

```
User completes chapter N
        |
        v
Frontend calls GET /api/v1/mentor/{course_slug}/status
        |
        v
Backend returns { mentor_available, wrong_answers_count, ... }
        |
        v (if available)
User clicks "Get Mentor Feedback"
        |
        v
Frontend calls POST /api/v1/mentor/{course_slug}/generate-quiz
  { include_hints: false, generate_extra: false }  // Free option
  OR
  { include_hints: true, generate_extra: true, extra_questions_count: 5 }  // AI option
        |
        v
Backend:
  1. WeakAreaAnalyzer.analyze_user_progress(user_id, course_slug)
  2. Get wrong answers from user_progress (FREE)
  3. If generate_extra=true: AIService.generate_extra_gap_questions() (AI cost)
  4. AIService.generate_feedback() (personalized)
        |
        v
Returns MentorFeedbackResponse:
  - analysis (user's weak areas)
  - feedback (personalized AI mentor text)
  - quiz:
      - wrong_answers: [5 questions user got wrong] (always free)
      - extra_questions: [5 AI questions] (only if generate_extra=true)
  - ai_generated (true if extra questions were generated)
```

---

## MongoDB Collections

### Existing (modified):
- `courses` - Add `slug` field (Step 1 - DONE)
- `user_progress` - Query wrong answers from `answers` array (no schema change)

### No New Collections
Wrong answers come from existing `user_progress.answers` where `is_correct=false`.
AI-generated extra questions are returned directly without caching (user pays per request).

---

## Testing After Each Step

| Step | Command | Expected |
|------|---------|----------|
| 1 | Create course, check slug | Slug like `topic-difficulty-abc123` (DONE) |
| 2 | `python run.py` | Starts without error (DONE) |
| 3 | `python -c "from app.models.mentor import *"` | No import error |
| 4 | Query wrong answers from user_progress | Returns wrong answers |
| 5 | Unit test analyzer | Returns analysis + wrong answers |
| 6 | `generate_extra=false` | Returns wrong answers only (FREE) |
| 6b | `generate_extra=true&provider=mock` | Returns wrong + extra questions |
| 7 | Check MongoDB `token_usage` | GAP_QUIZ logged (only if generate_extra) |
| 8 | `curl /api/v1/mentor/{slug}/status` | Returns status + wrong_answers_count |
| 9 | Open `/docs` | Mentor endpoints visible |
| 10 | Check `.env.example` | New vars documented |

---

## Implemented Enhancements

### Gap Quiz Caching

**Purpose:** Avoid re-spending AI tokens when user requests the same gap quiz.

**How it works:**
- Cache key: `user_id` + `course_slug` + `weak_areas_hash` + `include_hints`
- `weak_areas_hash` = MD5 of (chapter_numbers + scores)
- Cache automatically invalidates when weak areas change (user improves/declines)

**Collection:** `gap_quiz_cache`
```javascript
{
  user_id: "...",
  course_slug: "...",
  weak_areas_hash: "md5...",
  include_hints: true/false,
  extra_questions: [...],
  provider: "gemini",
  created_at: Date
}
```

**Files:**
- `backend/app/db/crud.py` - `get_cached_gap_quiz()`, `save_gap_quiz_cache()`
- `backend/app/routers/mentor.py` - Cache check before AI generation
- `backend/app/models/mentor.py` - `cache_hit` field in GapQuiz

---

### Question Pool Growth from Gap Quiz

**Purpose:** Reuse AI-generated gap quiz questions in future regular quizzes (free).

**How it works:**
1. When AI generates extra questions (costs tokens)
2. Immediately add them to chapter question collections
3. Tag with `source: "gap_quiz"` for tracking
4. Future chapter quizzes include these questions (free)

**Flow:**
```
Generate Gap Quiz (generate_extra=true)
    │
    ├── AI generates questions (tokens spent)
    ├── Save to gap_quiz_cache (for gap quiz reuse)
    ├── Add to questions collection (for regular quiz reuse) ←
    │
    └── Next chapter quiz includes these questions (FREE)
```

**Files:**
- `backend/app/db/crud.py` - `add_gap_quiz_questions_to_chapters()`
- `backend/app/routers/mentor.py` - Calls function after AI generation

**Question format in collection:**
```javascript
{
  id: "...",
  question_text: "...",
  correct_answer: "A",
  explanation: "...",
  difficulty: "medium",
  source: "gap_quiz",  // Tracks origin
  target_concept: "..."
}
```

---

## Frontend Implementation (Completed)

**Files Created:**
- `frontend/src/pages/Mentor.jsx` - Weak areas analysis + quiz options
- `frontend/src/pages/GapQuiz.jsx` - Interactive gap quiz
- `frontend/src/pages/GapQuizResults.jsx` - Results + answer review

**Files Modified:**
- `frontend/src/services/api.js` - Added `mentorAPI`
- `frontend/src/pages/Course.jsx` - Mentor button when available
- `frontend/src/App.jsx` - Added mentor routes

**Routes:**
- `/app/mentor/:courseSlug` - Mentor analysis page
- `/app/mentor/:courseSlug/quiz` - Gap quiz
- `/app/mentor/:courseSlug/results` - Quiz results

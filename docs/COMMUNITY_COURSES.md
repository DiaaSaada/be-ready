# Community Courses Feature - Implementation Plan

## Overview

Enable users to share courses publicly and browse/enroll in courses created by others.

**Key Decisions:**
- Courses are **private by default** (opt-in to make public)
- **AI-generated categories** with smart deduplication (avoid "Coding" vs "Programming")
- **AI-generated tags** (3-5 per course)
- **Enrollment copies** the course to user's library for progress tracking

---

## Phase 1: Backend Data Model Updates

### 1.1 Update CourseDocument
**File:** `backend/app/db/models.py`

Add fields:
```python
is_public: bool = Field(default=False)
tags: List[str] = Field(default_factory=list)
enrolled_count: int = Field(default=0)
original_course_id: Optional[str] = Field(default=None)  # If enrolled copy
creator_id: Optional[str] = Field(default=None)
```

### 1.2 Create Category Model
**File:** `backend/app/models/category.py` (NEW)

```python
class CategoryDocument(BaseModel):
    name: str              # "Programming"
    slug: str              # "programming"
    aliases: List[str]     # ["Coding", "Development", "Software"]
    course_count: int = 0
    created_at: datetime
    updated_at: datetime
```

**Seed Categories:** Programming, Physics, Marketing, Communication, Business, Design, Data Science, Mathematics, Languages, Personal Development

### 1.3 Update GenerateCourseResponse
**File:** `backend/app/models/course.py`

Add:
```python
tags: List[str] = Field(default_factory=list)
is_public: bool = Field(default=False)
```

---

## Phase 2: Category CRUD Operations

**File:** `backend/app/db/crud.py`

```python
CATEGORIES_COLLECTION = "categories"

async def get_or_create_category(suggested_name: str) -> str:
    """Match or create category. Returns canonical name."""

async def get_all_categories() -> List[Dict]:
    """Get all categories for filters."""

async def find_matching_category(suggested_name: str) -> Optional[str]:
    """Fuzzy match against existing categories and aliases."""

async def seed_categories():
    """Initialize default categories on app startup."""
```

---

## Phase 3: AI Service - Category & Tag Suggestion

### 3.1 Add UseCase
**File:** `backend/app/config.py`

```python
class UseCase(str, Enum):
    CATEGORY_SUGGESTION = "category_suggestion"

# Add settings
model_category_suggestion: str = "claude-3-5-haiku-20241022"
max_tokens_category: int = 200
```

### 3.2 Add Abstract Method
**File:** `backend/app/services/base_ai_service.py`

```python
@abstractmethod
async def suggest_category_and_tags(
    self,
    topic: str,
    chapters: List[Chapter],
    existing_categories: List[str],
    user_id: Optional[str] = None,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """Returns: {"category": "Programming", "tags": ["python", "fastapi"]}"""
    pass
```

### 3.3 Implement in All Providers
**Files:**
- `backend/app/services/claude_ai_service.py`
- `backend/app/services/openai_ai_service.py`
- `backend/app/services/gemini_ai_service.py`
- `backend/app/services/mock_ai_service.py`

**AI Prompt:**
```
Course topic: "{topic}"
Chapters: {chapter_titles}
Existing categories: {categories}

1. Pick the BEST matching category from existing list, or suggest a new one
2. Suggest 3-5 specific tags (lowercase, hyphenated)

Return JSON: {"category": "...", "tags": ["...", "..."]}
```

---

## Phase 4: Update Course Generation Flow

**File:** `backend/app/routers/courses.py`

In `generate_course()`:
1. After generating chapters, call `ai_service.suggest_category_and_tags()`
2. Call `crud.get_or_create_category()` to get/create canonical category
3. Save with `is_public=False`, `tags`, `category`

Update `save_course_for_user()` signature:
```python
async def save_course_for_user(
    ...,
    tags: List[str] = None,
    is_public: bool = False
)
```

---

## Phase 5: Community API Endpoints

**File:** `backend/app/routers/courses.py`

### 5.1 Browse Community Courses
```python
@router.get("/community")
async def get_community_courses(
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
) -> CommunityCoursesResponse
```

### 5.2 Enroll in Course
```python
@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: str,
    current_user = Depends(get_current_user)
) -> GenerateCourseResponse
```

### 5.3 Toggle Visibility
```python
@router.patch("/{course_id}/visibility")
async def update_course_visibility(
    course_id: str,
    is_public: bool,
    current_user = Depends(get_current_user)
)
```

### 5.4 Get Categories
```python
@router.get("/categories")
async def get_categories() -> List[Dict]
```

---

## Phase 6: Community CRUD Functions

**File:** `backend/app/db/crud.py`

```python
async def get_community_courses(
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 12
) -> Dict[str, Any]:
    """Returns: {"courses": [...], "total": int, "page": int, "pages": int}"""

async def copy_course_for_user(
    source_course_id: str,
    target_user_id: str
) -> Optional[Dict[str, str]]

async def update_course_visibility(
    course_id: str,
    user_id: str,
    is_public: bool
) -> bool

async def increment_enrolled_count(course_id: str)
```

---

## Phase 7: Response Models

**File:** `backend/app/models/responses.py`

```python
class CommunityCourseSummary(BaseModel):
    id: str
    slug: Optional[str]
    topic: str
    difficulty: str
    category: Optional[str]
    tags: List[str] = []
    total_chapters: int
    enrolled_count: int
    creator_name: Optional[str]
    created_at: datetime

class CommunityCoursesResponse(BaseModel):
    courses: List[CommunityCourseSummary]
    total: int
    page: int
    pages: int
    categories: List[str]
```

---

## Phase 8: Frontend Implementation

### 8.1 API Service
**File:** `frontend/src/services/api.js`

Add to `courseAPI`:
```javascript
getCommunity: async (filters = {}) => { ... },
enroll: async (courseId) => { ... },
setVisibility: async (courseId, isPublic) => { ... },
getCategories: async () => { ... },
```

### 8.2 Community Courses Page
**File:** `frontend/src/pages/CommunityCourses.jsx` (NEW)

Layout:
- Header with search bar
- Left sidebar: category buttons, difficulty filter
- Main area: 3-column course grid
- Pagination at bottom

State:
```javascript
const [filters, setFilters] = useState({ category: '', tags: [], difficulty: '', search: '' });
const [courses, setCourses] = useState([]);
const [categories, setCategories] = useState([]);
const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
```

### 8.3 Update CourseCard
**File:** `frontend/src/components/CourseCard.jsx`

Add props:
```jsx
function CourseCard({
  course,
  onClick,
  onDelete,
  onEnroll,       // NEW: callback for enroll
  showEnroll,     // NEW: show enroll button
  showCreator     // NEW: show creator name
})
```

### 8.4 Add Route
**File:** `frontend/src/App.jsx`

```jsx
<Route path="/app/community" element={
  <ProtectedRoute><CommunityCourses /></ProtectedRoute>
} />
```

### 8.5 Update Header
**File:** `frontend/src/components/Header.jsx`

Add nav link to "Community"

### 8.6 Course Detail - Visibility Toggle
**File:** `frontend/src/pages/Course.jsx`

Add toggle for owner to make course public/private

---

## Implementation Order

| Step | Task | Est. Time |
|------|------|-----------|
| 1 | Phase 1: Data model updates | 15 min |
| 2 | Phase 2: Category CRUD + seeding | 20 min |
| 3 | Phase 3: AI service method (all providers) | 30 min |
| 4 | Phase 4: Update course generation flow | 15 min |
| 5 | Phase 5-6: Community endpoints + CRUD | 30 min |
| 6 | Phase 7: Response models | 10 min |
| 7 | Phase 8: Frontend (page, components, routes) | 60 min |
| **Total** | | **~3 hours** |

---

## Critical Files Summary

**Backend:**
- `backend/app/db/models.py` - Add is_public, tags, enrolled_count
- `backend/app/models/category.py` - NEW: Category model
- `backend/app/db/crud.py` - Community queries, category management
- `backend/app/services/base_ai_service.py` - Add suggest_category_and_tags()
- `backend/app/services/*_ai_service.py` - Implement in all providers
- `backend/app/routers/courses.py` - Add /community, /enroll, /visibility
- `backend/app/models/responses.py` - Add CommunityCoursesResponse
- `backend/app/config.py` - Add CATEGORY_SUGGESTION UseCase

**Frontend:**
- `frontend/src/services/api.js` - Add community API methods
- `frontend/src/pages/CommunityCourses.jsx` - NEW: Browse page
- `frontend/src/components/CourseCard.jsx` - Add enroll support
- `frontend/src/App.jsx` - Add /app/community route
- `frontend/src/components/Header.jsx` - Add nav link
- `frontend/src/pages/Course.jsx` - Add visibility toggle

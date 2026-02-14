# AI Learning Platform

An AI-powered learning platform that generates personalized courses and quizzes from any topic.

## Features

- **Topic Validation** - AI validates topics before course generation
- **Course Generation** - Automatic chapter breakdown with AI
- **Study from Files** - Upload PDF, DOCX, or TXT files to generate courses from your own materials
- **Quiz Generation** - MCQ and True/False questions per chapter
- **User Authentication** - JWT-based signup/login
- **Progress Tracking** - Track answers, scores, and attempt counts with per-chapter progress display
- **Course Management** - Create, view, delete user courses
- **Auto-enrollment** - Users auto-enrolled in generated courses
- **Multi-Provider** - Supports Claude, OpenAI, and Mock providers
- **Smart Caching** - Save API costs with MongoDB caching

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: MongoDB with Motor (async)
- **AI Providers**: Claude, OpenAI, Mock
- **Auth**: JWT with bcrypt
- **Frontend**: React + Vite + Tailwind CSS

## Project Structure

```
be-ready/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Settings and AI config
│   │   ├── models/          # Pydantic models
│   │   ├── services/        # AI services, auth
│   │   ├── routers/         # API endpoints
│   │   ├── db/              # MongoDB operations
│   │   └── dependencies/    # Auth dependencies
│   ├── requirements.txt
│   └── run.py
├── frontend/                # React frontend
│   ├── src/
│   └── package.json
└── CLAUDE.md                # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- MongoDB (local or cloud instance)
- Anthropic API key (or OpenAI API key)

### 2. Installation

```bash
# Clone or navigate to the project directory
cd ai-learning-platform

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
MONGODB_URL=mongodb://localhost:27017
```

### 4. Run the Application

```bash
# Option 1: Using the run script
python run.py

# Option 2: Using uvicorn directly
uvicorn app.main:app --reload

# Option 3: Using the main module
python -m app.main
```

The API will be available at: `http://localhost:8000`

### 5. Test the API

Open your browser and visit:
- API Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

Or use curl:
```bash
curl http://localhost:8000/health
```

## API Endpoints

### Auth
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user

### Courses
- `POST /api/v1/courses/generate` - Generate course from topic (auth required)
- `POST /api/v1/courses/generate-from-files` - Generate course from uploaded files (PDF, DOCX, TXT)
- `POST /api/v1/courses/validate` - Validate topic before generation
- `GET /api/v1/courses/my-courses` - Get user's created courses
- `GET /api/v1/courses/{id}` - Get course by ID
- `DELETE /api/v1/courses/{id}` - Delete a course

### Questions
- `POST /api/v1/questions/generate` - Generate quiz questions
- `POST /api/v1/questions/analyze-count` - Get recommended question count

### Progress
- `POST /api/v1/progress/submit` - Submit answer
- `GET /api/v1/progress/` - Get user progress

### My Courses (Enrolled)
- `GET /api/v1/my-courses/` - Get enrolled courses

## Development Roadmap

### Completed
- [x] Project setup and configuration
- [x] MongoDB integration
- [x] Chapter generation with Claude/OpenAI
- [x] Question generation service
- [x] Progress tracking system
- [x] Caching layer
- [x] User authentication (JWT)
- [x] Course management (CRUD)
- [x] Auto-enrollment on generation
- [x] File upload processing (PDF, DOCX, TXT)
- [x] Gemini AI provider
- [x] Frontend integration
- [x] Multi-file document analysis with source tracking
- [x] Language detection and multi-language content generation (Arabic, English, etc.)

### In Progress
- [ ] AI mentor feedback
- [ ] RAG system for contextual help (https://github.com/yichuan-w/LEANN)
- [ ] Chapter verification with secondary LLM
- [ ] Improve the topic title before generation
- [ ] Async job queue with RabbitMQ for chapter/question generation
- [ ] Prometheus + Grafana for metrics & dashboards (server health, API performance)
- [ ] Rate limiting
- [ ] Notifications ("Time to study!" reminders, quick tips to keep users engaged)
- [ ] Human feedback (thumbs up/down course based on how good the quility and coverage)
- [ ] GitHub Actions (CI/CD pipeline)
- [ ] Gamification
- [ ] Community Courses gallery of already generated courses other subscribed users can use without paying for LLM tokens
quizes 
- [ ] Intereduce Grphics and ArtWorks
- [ ] Bring your own LLM key
- [ ] Invite studets to already generated course by a teacher and email the teacher when each student submit his final result



### Future Features

| Phase | Feature | Priority | Description |
|-------|---------|----------|-------------|
| 1 | Platform Token System | High | Purchase tokens (1$ = N tokens), balance display, top-up |
| 1 | Token Usage & Logging | High | Track usage per user/operation/course, provider-specific rates |
| 2 | Payment & Subscriptions | High | Stripe/PayPal integration, monthly/yearly plans |
| 3 | Paid & Free Tier | High | AI generation for paid users, community courses for free |
| 3 | Community Courses | Medium | Public course library, browse by topic, ratings |
| 4 | Social Login | Medium | Google, Apple, LinkedIn OAuth |
| 5 | Enhanced User Profile | Medium | Age, education level, goals for personalized content |
| 6 | Human Mentor Accounts | Low | Generate/review courses, referral codes, student tracking |
| 7 | AI Flashcards | High | Auto-generate flashcards from course chapters for quick review |
| 7 | Spaced Repetition | High | Smart review scheduling (SM-2 algorithm) to improve retention |
| 7 | MindMap | High | improve grasping |
| 8 | AI Tutor Chat | High | Chat interface to ask questions about course content (RAG-based) |
| 8 | YouTube Video Support | High | Generate courses from YouTube video URLs via transcript extraction |
| 9 | Study Schedule Generator | Medium | AI creates personalized study plan based on exam date and availability |
| 9 | AI Summarization | Medium | Generate condensed chapter summaries for quick review before exams |
| 10 | Multi-language Support | Medium | Generate courses/quizzes in 20+ languages |
| 10 | LMS Integration (Canvas) | Medium | Import courses/assignments from Canvas, Blackboard via API |
| 11 | Chrome Extension | Low | Right-click any webpage to generate a course from its content |
| 11 | Mobile App (PWA) | Low | Installable progressive web app with offline support |
| 11 | Imprve animations and sho usefull qutes | Low | enhance XP |
| 12 | Generate ArtWork images, infoGraphs and diagrams for each chapter | Low | enhance XP |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Anthropic API key | Required |
| OPENAI_API_KEY | OpenAI API key | Optional |
| JWT_SECRET_KEY | Secret for JWT tokens | Required |
| MONGODB_URL | MongoDB connection URL | mongodb://localhost:27017 |
| MONGODB_DB_NAME | Database name | ai_learning_platform |
| DEFAULT_AI_PROVIDER | AI provider (claude/openai/mock) | mock |

## Contributing

This is a work in progress. We're building it step-by-step!

## License

MIT License

## Contact

For questions or suggestions, please open an issue.
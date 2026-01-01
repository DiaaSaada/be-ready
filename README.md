# AI Learning Platform

An AI-powered learning platform that generates personalized courses and quizzes from any topic.

## Features

- **Topic Validation** - AI validates topics before course generation
- **Course Generation** - Automatic chapter breakdown with AI
- **Quiz Generation** - MCQ and True/False questions per chapter
- **User Authentication** - JWT-based signup/login
- **Progress Tracking** - Track answers and scores
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

- [x] Project setup and configuration
- [x] MongoDB integration
- [x] Chapter generation with Claude/OpenAI
- [x] Question generation service
- [x] Progress tracking system
- [x] Caching layer
- [x] User authentication (JWT)
- [x] Course management (CRUD)
- [x] Auto-enrollment on generation
- [ ] PDF processing service
- [ ] AI mentor feedback
- [ ] RAG system for contextual help  (https://github.com/yichuan-w/LEANN)
- [ ] Gemini AI provider
- [ ] Chapter verification with secondary LLM
- [x] Frontend integration
- [ ] Improve the topic title before generation

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
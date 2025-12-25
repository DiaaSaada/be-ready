# AI Learning Platform 🎓🤖

An AI-powered learning platform that generates adaptive quizzes and provides personalized mentoring.

## Features

- 📄 PDF document processing and analysis
- 📚 Automatic chapter breakdown
- ❓ AI-generated quizzes (MCQ, True/False)
- 📊 Progress tracking and analytics
- 🎯 Adaptive learning recommendations
- 💾 Smart caching to save API costs

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: Claude/OpenAI API
- **Vector Store**: ChromaDB
- **Embeddings**: Sentence Transformers

## Project Structure

```
ai-learning-platform/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   ├── routers/             # API endpoints
│   ├── db/                  # Database layer
│   └── utils/               # Helper functions
├── tests/                   # Test files
├── uploads/                 # Uploaded files directory
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── run.py                   # Application runner
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

## API Endpoints (Coming Soon)

- `POST /api/v1/courses/upload` - Upload PDF and generate course
- `GET /api/v1/courses/{course_id}` - Get course details
- `GET /api/v1/courses/{course_id}/chapters` - Get all chapters
- `POST /api/v1/progress/answer` - Submit an answer
- `GET /api/v1/progress/{user_id}/{course_id}` - Get user progress
- `GET /api/v1/progress/{user_id}/{course_id}/feedback` - Get AI mentor feedback

## Development Roadmap

- [x] Project setup and configuration
- [ ] MongoDB integration
- [ ] PDF processing service
- [ ] Chapter generation with Claude
- [ ] Question generation service
- [ ] Progress tracking system
- [ ] AI mentor feedback
- [ ] RAG system for contextual help
- [ ] Caching layer
- [ ] User authentication
- [ ] Frontend integration

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Your Anthropic API key | Required |
| MONGODB_URL | MongoDB connection URL | mongodb://localhost:27017 |
| MONGODB_DB_NAME | Database name | ai_learning_platform |
| MAX_UPLOAD_SIZE | Max file upload size (bytes) | 10485760 (10MB) |
| DEFAULT_LLM_MODEL | Claude model to use | claude-sonnet-4-20250514 |

## Contributing

This is a work in progress. We're building it step-by-step!

## License

MIT License

## Contact

For questions or suggestions, please open an issue.
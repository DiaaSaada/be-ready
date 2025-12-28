# BE-READY Monorepo

AI-powered learning platform with course generation and quiz questions.

## Structure

```
be-ready/
├── backend/    # FastAPI backend (Python)
├── frontend/   # React + Vite frontend
└── CLAUDE.md   # This file
```

## Quick Start

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python run.py
# → http://localhost:8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Backend

See [backend/CLAUDE.md](backend/CLAUDE.md) for full documentation.

- FastAPI + Python 3.12
- MongoDB for storage
- Claude/OpenAI for AI generation

## Frontend

See [frontend/CLAUDE.md](frontend/CLAUDE.md) for full documentation.

- React 18 + Vite
- Tailwind CSS
- React Router

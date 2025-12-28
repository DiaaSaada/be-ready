# Frontend - Be Ready

React + Vite + Tailwind CSS frontend for the AI Learning Platform.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Client-side routing
- **Axios** - API calls

## Commands

```bash
# Install dependencies
npm install

# Run development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page components
│   │   ├── Landing.jsx   # Home page with CTA
│   │   ├── NewCourse.jsx # Create new course form
│   │   └── Course.jsx    # Display generated course
│   ├── services/
│   │   └── api.js        # Backend API calls
│   ├── App.jsx           # Router setup
│   ├── main.jsx          # Entry point
│   └── index.css         # Tailwind imports
├── public/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Landing | Hero page with "Get Started" button |
| `/app` | NewCourse | Topic input, difficulty selection, validation |
| `/app/course` | Course | Display generated chapters |

## API Integration

Backend runs on `http://localhost:8000`. The API service (`src/services/api.js`) provides:

```javascript
// Course endpoints
courseAPI.validate(topic)           // Validate topic
courseAPI.generate(topic, difficulty) // Generate course

// Question endpoints
questionAPI.generate(...)           // Generate questions for chapter
```

## Development

1. Start backend first:
   ```bash
   cd backend
   python run.py
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:5173

## Environment Variables

Create `.env` file if needed:

```env
VITE_API_URL=http://localhost:8000
```

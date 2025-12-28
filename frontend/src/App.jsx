import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import NewCourse from './pages/NewCourse';
import Course from './pages/Course';
import Quiz from './pages/Quiz';
import QuizResults from './pages/QuizResults';
import Progress from './pages/Progress';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<NewCourse />} />
        <Route path="/app/new" element={<NewCourse />} />
        <Route path="/app/course" element={<Course />} />
        <Route path="/app/quiz" element={<Quiz />} />
        <Route path="/app/quiz/results" element={<QuizResults />} />
        <Route path="/app/progress" element={<Progress />} />
      </Routes>
    </Router>
  );
}

export default App;

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import NewCourse from './pages/NewCourse';
import MyCourses from './pages/MyCourses';
import Course from './pages/Course';
import Quiz from './pages/Quiz';
import QuizResults from './pages/QuizResults';
import Progress from './pages/Progress';
import TokenUsage from './pages/TokenUsage';
import Mentor from './pages/Mentor';
import GapQuiz from './pages/GapQuiz';
import GapQuizResults from './pages/GapQuizResults';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected routes */}
          <Route path="/app" element={
            <ProtectedRoute>
              <NewCourse />
            </ProtectedRoute>
          } />
          <Route path="/app/new" element={
            <ProtectedRoute>
              <NewCourse />
            </ProtectedRoute>
          } />
          <Route path="/app/my-courses" element={
            <ProtectedRoute>
              <MyCourses />
            </ProtectedRoute>
          } />
          <Route path="/app/course/:courseSlug" element={
            <ProtectedRoute>
              <Course />
            </ProtectedRoute>
          } />
          <Route path="/app/course/:courseSlug/ch/:chapterNumber/quiz" element={
            <ProtectedRoute>
              <Quiz />
            </ProtectedRoute>
          } />
          <Route path="/app/course/:courseSlug/ch/:chapterNumber/results" element={
            <ProtectedRoute>
              <QuizResults />
            </ProtectedRoute>
          } />
          <Route path="/app/progress" element={
            <ProtectedRoute>
              <Progress />
            </ProtectedRoute>
          } />
          <Route path="/app/token-usage" element={
            <ProtectedRoute>
              <TokenUsage />
            </ProtectedRoute>
          } />
          <Route path="/app/mentor/:courseSlug" element={
            <ProtectedRoute>
              <Mentor />
            </ProtectedRoute>
          } />
          <Route path="/app/mentor/:courseSlug/quiz" element={
            <ProtectedRoute>
              <GapQuiz />
            </ProtectedRoute>
          } />
          <Route path="/app/mentor/:courseSlug/results" element={
            <ProtectedRoute>
              <GapQuizResults />
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import NewCourse from './pages/NewCourse';
import Course from './pages/Course';
import Quiz from './pages/Quiz';
import QuizResults from './pages/QuizResults';
import Progress from './pages/Progress';

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
          <Route path="/app/course" element={
            <ProtectedRoute>
              <Course />
            </ProtectedRoute>
          } />
          <Route path="/app/quiz" element={
            <ProtectedRoute>
              <Quiz />
            </ProtectedRoute>
          } />
          <Route path="/app/quiz/results" element={
            <ProtectedRoute>
              <QuizResults />
            </ProtectedRoute>
          } />
          <Route path="/app/progress" element={
            <ProtectedRoute>
              <Progress />
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

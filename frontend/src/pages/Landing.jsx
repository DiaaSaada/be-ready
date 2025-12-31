import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Landing() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center">
      <div className="text-center text-white px-4">
        {/* Logo/Icon */}
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto bg-white rounded-2xl flex items-center justify-center shadow-lg">
            <span className="text-4xl">📚</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl font-bold mb-4">
          Be Ready
        </h1>

        {/* Subtitle */}
        <p className="text-xl text-blue-100 mb-8 max-w-md mx-auto">
          AI-powered learning platform. Generate personalized courses and quizzes on any topic.
        </p>

        {/* Features */}
        <div className="flex flex-wrap justify-center gap-4 mb-10 text-sm">
          <span className="bg-white/20 px-4 py-2 rounded-full">
            ✨ AI-Generated Courses
          </span>
          <span className="bg-white/20 px-4 py-2 rounded-full">
            📝 Smart Quizzes
          </span>
          <span className="bg-white/20 px-4 py-2 rounded-full">
            🎯 Any Topic
          </span>
        </div>

        {/* CTA Button */}
        <Link
          to={isAuthenticated ? "/app" : "/signup"}
          className="inline-block bg-white text-blue-600 font-semibold px-8 py-4 rounded-xl text-lg shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200"
        >
          {isLoading ? 'Loading...' : isAuthenticated ? 'Go to App →' : 'Get Started →'}
        </Link>

        {/* Footer text */}
        <p className="mt-12 text-blue-200 text-sm">
          © 2025 Be Ready. All rights reserved.
        </p>
      </div>
    </div>
  );
}

export default Landing;

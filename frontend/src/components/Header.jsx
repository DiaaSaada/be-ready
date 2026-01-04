import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/app" className="text-xl font-bold text-blue-600">
          Be Ready
        </Link>

        <div className="flex items-center gap-4">
          <Link
            to="/app"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            New Course
          </Link>
          <Link
            to="/app/my-courses"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            My Courses
          </Link>
          <Link
            to="/app/progress"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            My Progress
          </Link>
          <Link
            to="/app/token-usage"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Token Usage
          </Link>

          {/* User info and logout */}
          <div className="flex items-center gap-3 ml-4 pl-4 border-l border-gray-200">
            <span className="text-sm text-gray-700 font-medium">
              {user?.name}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;

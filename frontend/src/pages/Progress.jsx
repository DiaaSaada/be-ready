import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { progressAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';

function Progress() {
  const { user } = useAuth();
  const [progress, setProgress] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setIsLoading(true);
        const userId = user?.id;

        // Fetch progress and summary in parallel
        const [progressData, summaryData] = await Promise.all([
          progressAPI.getAll(userId),
          progressAPI.getSummary(userId),
        ]);

        setProgress(progressData.progress || []);
        setSummary(summaryData);
      } catch (err) {
        console.error('Failed to load progress:', err);
        setError('Failed to load progress');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProgress();
  }, []);

  // Get score color
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  // Group progress by course
  const groupedProgress = progress.reduce((acc, item) => {
    const key = `${item.course_topic}-${item.difficulty}`;
    if (!acc[key]) {
      acc[key] = {
        topic: item.course_topic,
        difficulty: item.difficulty,
        chapters: [],
      };
    }
    acc[key].chapters.push(item);
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Progress</h1>
        <p className="text-gray-600 mb-8">Track your quiz scores and learning journey</p>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-4"></div>
            <p className="text-gray-600">Loading progress...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Summary Card */}
        {!isLoading && summary && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-blue-600">{summary.total_quizzes_completed}</p>
                <p className="text-sm text-gray-600">Quizzes Completed</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-green-600">{summary.total_correct}</p>
                <p className="text-sm text-gray-600">Correct Answers</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-purple-600">{summary.total_questions_answered}</p>
                <p className="text-sm text-gray-600">Total Questions</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-orange-600">{Math.round(summary.average_score * 100)}%</p>
                <p className="text-sm text-gray-600">Average Score</p>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && progress.length === 0 && (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No progress yet</h2>
            <p className="text-gray-600 mb-6">Complete some quizzes to track your progress</p>
            <Link
              to="/app"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
            >
              Start Learning
            </Link>
          </div>
        )}

        {/* Progress by Course */}
        {!isLoading && Object.values(groupedProgress).map((course) => (
          <div key={`${course.topic}-${course.difficulty}`} className="bg-white rounded-xl shadow-sm p-6 mb-4">
            {/* Course Header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 capitalize">
                  {course.topic}
                </h2>
                <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                  course.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                  course.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {course.difficulty}
                </span>
              </div>
              <span className="text-sm text-gray-500">
                {course.chapters.length} chapter{course.chapters.length !== 1 ? 's' : ''} completed
              </span>
            </div>

            {/* Chapters List */}
            <div className="space-y-3">
              {course.chapters
                .sort((a, b) => a.chapter_number - b.chapter_number)
                .map((item) => (
                  <div
                    key={`${item.chapter_number}-${item.completed_at}`}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-medium text-sm">
                        {item.chapter_number}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">{item.chapter_title}</p>
                        <p className="text-xs text-gray-500">
                          {item.completed_at && new Date(item.completed_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(item.score_percent)}`}>
                        {item.score_percent}%
                      </span>
                      <span className="text-xs text-gray-500">
                        {item.correct_answers}/{item.total_questions}
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}

        {/* Back Button */}
        {!isLoading && progress.length > 0 && (
          <div className="mt-8 text-center">
            <Link
              to="/app"
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
            >
              Create New Course
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}

export default Progress;

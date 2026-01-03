import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { courseAPI, progressAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

function Course() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [course, setCourse] = useState(null);
  const [progress, setProgress] = useState({}); // Map: chapterNumber -> progressData
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCourseAndProgress = async () => {
      try {
        setLoading(true);
        const data = await courseAPI.getById(courseId);
        setCourse(data);

        // Fetch progress for this course
        if (user?.id && data?.topic && data?.difficulty) {
          try {
            const progressData = await progressAPI.getCourse(
              user.id,
              data.topic,
              data.difficulty
            );
            // Convert array to map by chapter_number
            const progressMap = {};
            (progressData.progress || []).forEach((p) => {
              progressMap[p.chapter_number] = p;
            });
            setProgress(progressMap);
          } catch (progressErr) {
            // Progress fetch failure is not critical - just log it
            console.warn('Failed to fetch progress:', progressErr);
          }
        }
      } catch (err) {
        console.error('Failed to fetch course:', err);
        setError('Course not found or you do not have access.');
      } finally {
        setLoading(false);
      }
    };

    fetchCourseAndProgress();
  }, [courseId, user?.id]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Loading course...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !course) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <p className="text-red-600 mb-4">{error || 'Course not found'}</p>
          <Link
            to="/app/my-courses"
            className="text-blue-600 hover:underline"
          >
            Back to My Courses
          </Link>
        </div>
      </div>
    );
  }

  const handleStartQuiz = (chapter) => {
    navigate('/app/quiz', {
      state: {
        topic: course.topic,
        difficulty: course.difficulty,
        chapter: chapter,
      },
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Course Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {course.topic}
              </h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  course.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                  course.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {course.difficulty}
                </span>
                <span>{course.total_chapters} chapters</span>
                <span>~{course.estimated_study_hours} hours</span>
              </div>
            </div>
          </div>

          {/* Course Meta */}
          {course.config && (
            <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
              <span>{course.config.time_per_chapter_minutes} min per chapter</span>
              <span className="mx-2">•</span>
              <span>{course.config.chapter_depth} depth</span>
            </div>
          )}
        </div>

        {/* Chapters List */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Chapters</h2>

          {course.chapters?.map((chapter, index) => {
            const chapterNum = chapter.number || index + 1;
            const chapterProgress = progress[chapterNum];

            // Score color based on best score
            const getScoreColor = (score) => {
              if (score >= 80) return 'bg-green-100 text-green-700';
              if (score >= 60) return 'bg-yellow-100 text-yellow-700';
              return 'bg-red-100 text-red-700';
            };

            return (
              <div
                key={chapterNum}
                className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-4">
                  {/* Chapter Number - with checkmark if completed */}
                  <div
                    className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-bold ${
                      chapterProgress
                        ? 'bg-green-100 text-green-600'
                        : 'bg-blue-100 text-blue-600'
                    }`}
                  >
                    {chapterProgress ? (
                      <svg
                        className="w-5 h-5"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      chapterNum
                    )}
                  </div>

                  {/* Chapter Content */}
                  <div className="flex-grow">
                    <h3 className="font-semibold text-gray-900 mb-1">
                      {chapter.title}
                    </h3>
                    <p className="text-gray-600 text-sm mb-3">
                      {chapter.summary}
                    </p>

                    {/* Progress Display */}
                    {chapterProgress && (
                      <div className="flex items-center gap-3 mb-3 p-2 bg-gray-50 rounded-lg">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(
                            chapterProgress.best_score_percent
                          )}`}
                        >
                          Best: {chapterProgress.best_score_percent}%
                        </span>
                        <span className="text-xs text-gray-500">
                          {chapterProgress.correct_answers}/
                          {chapterProgress.total_questions} correct
                        </span>
                        <span className="text-xs text-gray-400">
                          {chapterProgress.attempt_count} attempt
                          {chapterProgress.attempt_count !== 1 ? 's' : ''}
                        </span>
                      </div>
                    )}

                    {/* Key Concepts */}
                    {chapter.key_concepts?.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {chapter.key_concepts.map((concept, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md"
                          >
                            {concept}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Time Estimate & Quiz Button */}
                    <div className="flex items-center justify-between mt-3">
                      {chapter.estimated_time_minutes && (
                        <p className="text-xs text-gray-400">
                          ⏱ {chapter.estimated_time_minutes} min
                        </p>
                      )}
                      <button
                        onClick={() => handleStartQuiz(chapter)}
                        className={`px-4 py-2 text-white text-sm font-medium rounded-lg transition-colors ${
                          chapterProgress
                            ? 'bg-blue-600 hover:bg-blue-700'
                            : 'bg-green-600 hover:bg-green-700'
                        }`}
                      >
                        {chapterProgress ? 'Retake Quiz' : 'Start Quiz'} →
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Actions */}
        <div className="mt-8 flex justify-center">
          <Link
            to="/app"
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Another Course
          </Link>
        </div>
      </main>
    </div>
  );
}

export default Course;

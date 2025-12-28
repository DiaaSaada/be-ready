import { useLocation, Link, Navigate, useNavigate } from 'react-router-dom';

function Course() {
  const location = useLocation();
  const navigate = useNavigate();
  const course = location.state?.course;

  // If no course data, redirect to new course page
  if (!course) {
    return <Navigate to="/app" replace />;
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
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-blue-600">
            📚 Be Ready
          </Link>
          <Link
            to="/app"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            ← New Course
          </Link>
        </div>
      </header>

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

          {course.chapters?.map((chapter, index) => (
            <div
              key={chapter.number || index}
              className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4">
                {/* Chapter Number */}
                <div className="flex-shrink-0 w-10 h-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center font-bold">
                  {chapter.number || index + 1}
                </div>

                {/* Chapter Content */}
                <div className="flex-grow">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {chapter.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-3">
                    {chapter.summary}
                  </p>

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
                      className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Start Quiz →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
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

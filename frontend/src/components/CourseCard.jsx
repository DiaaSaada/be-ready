import { useState } from 'react';

/**
 * Format date to relative time or readable format
 */
function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

/**
 * Get difficulty badge styles
 */
function getDifficultyStyles(difficulty) {
  switch (difficulty) {
    case 'beginner':
      return 'bg-green-100 text-green-800';
    case 'intermediate':
      return 'bg-yellow-100 text-yellow-800';
    case 'advanced':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * CourseCard - Displays a course summary card
 *
 * @param {Object} props
 * @param {Object} props.course - Course data
 * @param {Function} props.onClick - Called when card is clicked
 * @param {Function} [props.onDelete] - Called when delete button is clicked
 */
function CourseCard({ course, onClick, onDelete }) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const {
    id,
    topic,
    difficulty,
    complexity_score,
    total_chapters,
    questions_generated,
    created_at
  } = course;

  const handleCardClick = () => {
    if (!showDeleteConfirm) {
      onClick(course);
    }
  };

  const handleDeleteClick = (e) => {
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = (e) => {
    e.stopPropagation();
    onDelete(course);
    setShowDeleteConfirm(false);
  };

  const handleCancelDelete = (e) => {
    e.stopPropagation();
    setShowDeleteConfirm(false);
  };

  return (
    <div
      onClick={handleCardClick}
      className="relative bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-4 cursor-pointer border border-gray-100"
    >
      {/* Delete button */}
      {onDelete && !showDeleteConfirm && (
        <button
          onClick={handleDeleteClick}
          className="absolute top-3 right-3 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
          title="Delete course"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      )}

      {/* Delete confirmation */}
      {showDeleteConfirm && (
        <div className="absolute inset-0 bg-white bg-opacity-95 rounded-lg flex flex-col items-center justify-center gap-3 z-10">
          <p className="text-sm text-gray-700 font-medium">Delete this course?</p>
          <div className="flex gap-2">
            <button
              onClick={handleConfirmDelete}
              className="px-3 py-1.5 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
            >
              Delete
            </button>
            <button
              onClick={handleCancelDelete}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Topic title */}
      <h3 className="text-lg font-semibold text-gray-900 mb-2 pr-8">
        {topic}
      </h3>

      {/* Badges row */}
      <div className="flex flex-wrap gap-2 mb-3">
        {/* Difficulty badge */}
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getDifficultyStyles(difficulty)}`}
        >
          {difficulty}
        </span>

        {/* Quiz ready badge */}
        {questions_generated && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <svg
              className="w-3 h-3 mr-1"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            Quiz Ready
          </span>
        )}
      </div>

      {/* Stats row */}
      <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
        <span className="flex items-center">
          <svg
            className="w-4 h-4 mr-1 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
          {total_chapters} chapters
        </span>

        {complexity_score !== null && (
          <span className="text-gray-500">
            Complexity: {complexity_score}/10
          </span>
        )}
      </div>

      {/* Created date */}
      <p className="text-xs text-gray-400">
        {formatDate(created_at)}
      </p>
    </div>
  );
}

export default CourseCard;

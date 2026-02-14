import { useState, useEffect } from 'react';
import { useLocation, Link, Navigate, useParams } from 'react-router-dom';
import { progressAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';

function QuizResults() {
  const location = useLocation();
  const { courseSlug, chapterNumber } = useParams();
  const { user } = useAuth();
  const { topic, difficulty, chapter, questions, answers } = location.state || {};

  // Save status
  const [saveStatus, setSaveStatus] = useState('pending'); // pending, saving, saved, error

  // Redirect if no data
  if (!questions || !answers) {
    return <Navigate to="/app" replace />;
  }

  // Calculate score
  const totalQuestions = questions.length;
  const correctCount = Object.values(answers).filter(a => a.isCorrect).length;
  const scorePercent = Math.round((correctCount / totalQuestions) * 100);

  // Save progress on mount
  useEffect(() => {
    const saveProgress = async () => {
      try {
        setSaveStatus('saving');
        const userId = user?.id;

        // Format answers for API
        const formattedAnswers = Object.entries(answers).map(([index, answer]) => ({
          question_index: parseInt(index),
          question_id: questions[index]?.id || null,
          question_text: questions[index]?.question || '',
          selected: answer.selected,
          correct: answer.correct,
          is_correct: answer.isCorrect,
        }));

        await progressAPI.submit(userId, {
          topic,
          difficulty,
          chapterNumber: chapter.number,
          chapterTitle: chapter.title,
          answers: formattedAnswers,
          totalQuestions,
          correctCount,
        });

        setSaveStatus('saved');
      } catch (err) {
        console.error('Failed to save progress:', err);
        setSaveStatus('error');
      }
    };

    saveProgress();
  }, []); // Run once on mount

  // Get score message and color
  const getScoreInfo = () => {
    if (scorePercent >= 80) {
      return { message: 'Excellent!', color: 'text-green-600', bg: 'bg-green-100' };
    } else if (scorePercent >= 60) {
      return { message: 'Good job!', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    } else {
      return { message: 'Keep practicing!', color: 'text-red-600', bg: 'bg-red-100' };
    }
  };

  const scoreInfo = getScoreInfo();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Score Card */}
        <div className="bg-white rounded-xl shadow-sm p-8 text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {chapter.title}
          </h1>
          <p className="text-gray-500 mb-6">Quiz Complete</p>

          {/* Score Circle */}
          <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${scoreInfo.bg} mb-4`}>
            <span className={`text-4xl font-bold ${scoreInfo.color}`}>
              {scorePercent}%
            </span>
          </div>

          <p className={`text-xl font-semibold ${scoreInfo.color} mb-2`}>
            {scoreInfo.message}
          </p>
          <p className="text-gray-600">
            You got {correctCount} out of {totalQuestions} questions correct
          </p>

          {/* Save Status */}
          <div className="mt-4 text-sm">
            {saveStatus === 'saving' && (
              <span className="text-gray-500">Saving progress...</span>
            )}
            {saveStatus === 'saved' && (
              <span className="text-green-600">Progress saved</span>
            )}
            {saveStatus === 'error' && (
              <span className="text-red-600">Failed to save progress</span>
            )}
          </div>
        </div>

        {/* Question Review */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Review Answers</h2>

          {questions.map((question, index) => {
            const answer = answers[index];
            const isCorrect = answer?.isCorrect;

            return (
              <div
                key={index}
                className={`bg-white rounded-xl shadow-sm p-5 border-l-4 ${isCorrect ? 'border-green-500' : 'border-red-500'
                  }`}
              >
                {/* Question Number & Type */}
                <div className="flex items-center gap-2 mb-2">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white ${isCorrect ? 'bg-green-500' : 'bg-red-500'
                    }`}>
                    {index + 1}
                  </span>
                  <span className="text-xs text-gray-400 uppercase">
                    {question.type === 'mcq' ? 'Multiple Choice' : 'True/False'}
                  </span>
                </div>

                {/* Question Text */}
                <p className="text-gray-900 font-medium mb-3">
                  {question.question}
                </p>

                {/* Answer Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <span className="text-gray-500 w-24 flex-shrink-0">Your answer:</span>
                    <span className={isCorrect ? 'text-green-600' : 'text-red-600'}>
                      {question.type === 'mcq' ? (
                        <>
                          {answer?.selected}
                          {answer?.selected && question.options?.[answer.selected.charCodeAt(0) - 65] && (
                            <span className="text-gray-500 ml-1">
                              - {question.options[answer.selected.charCodeAt(0) - 65]}
                            </span>
                          )}
                        </>
                      ) : (
                        answer?.selected
                      )}
                    </span>
                  </div>

                  {!isCorrect && (
                    <div className="flex items-start gap-2">
                      <span className="text-gray-500 w-24 flex-shrink-0">Correct:</span>
                      <span className="text-green-600">
                        {question.type === 'mcq' ? (
                          <>
                            {question.correct_answer}
                            {question.options?.[question.correct_answer.charCodeAt(0) - 65] && (
                              <span className="text-gray-500 ml-1">
                                - {question.options[question.correct_answer.charCodeAt(0) - 65]}
                              </span>
                            )}
                          </>
                        ) : (
                          question.correct_answer
                        )}
                      </span>
                    </div>
                  )}

                  {/* Explanation */}
                  {question.explanation && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <p className="text-gray-600">{question.explanation}</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to={`/app/course/${courseSlug}/ch/${chapterNumber}/quiz`}
            state={{ topic, difficulty, chapter }}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors text-center"
          >
            Try Again
          </Link>
          <Link
            to={`/app/course/${courseSlug}`}
            className="px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors text-center"
          >
            Back to Course
          </Link>
          <Link
            to="/app/progress"
            className="px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition-colors text-center"
          >
            My Progress
          </Link>
        </div>
      </main>
    </div>
  );
}

export default QuizResults;

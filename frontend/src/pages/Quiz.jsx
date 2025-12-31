import { useState, useEffect } from 'react';
import { useLocation, Link, Navigate, useNavigate } from 'react-router-dom';
import { questionAPI } from '../services/api';

function Quiz() {
  const location = useLocation();
  const navigate = useNavigate();
  const { topic, difficulty, chapter } = location.state || {};

  // Quiz state
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);

  // Redirect if no chapter data
  if (!chapter) {
    return <Navigate to="/app" replace />;
  }

  // Fetch questions on mount
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const result = await questionAPI.generate(
          topic,
          difficulty,
          chapter.number,
          chapter.title,
          chapter.key_concepts || [],
          true // chunked mode
        );

        // Map backend format to frontend format
        // Backend: mcq_questions, true_false_questions, question_text
        // Frontend: mcq, true_false, question
        const mcqQuestions = (result.mcq_questions || []).map(q => ({
          ...q,
          type: 'mcq',
          question: q.question_text,
          // Strip "A) ", "B) " etc. from options for cleaner display
          options: q.options?.map(opt => opt.replace(/^[A-D]\)\s*/, '')) || [],
        }));

        const tfQuestions = (result.true_false_questions || []).map(q => ({
          ...q,
          type: 'true_false',
          question: q.question_text,
          // Backend stores boolean, convert to string for comparison
          correct_answer: q.correct_answer === true ? 'True' : 'False',
        }));

        // Combine and shuffle questions
        const allQuestions = [...mcqQuestions, ...tfQuestions];
        const shuffled = allQuestions.sort(() => Math.random() - 0.5);
        setQuestions(shuffled);
      } catch (err) {
        console.error('Failed to load questions:', err);
        setError(err.response?.data?.detail || 'Failed to load questions');
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuestions();
  }, [topic, difficulty, chapter]);

  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;
  const progress = totalQuestions > 0 ? ((currentIndex) / totalQuestions) * 100 : 0;

  const handleAnswerSelect = (answer) => {
    if (showFeedback) return; // Prevent changing answer after feedback shown
    setSelectedAnswer(answer);
  };

  const handleSubmitAnswer = () => {
    if (selectedAnswer === null) return;

    // Store the answer
    setAnswers(prev => ({
      ...prev,
      [currentIndex]: {
        selected: selectedAnswer,
        correct: currentQuestion.correct_answer,
        isCorrect: selectedAnswer === currentQuestion.correct_answer,
      },
    }));

    setShowFeedback(true);
  };

  const handleNextQuestion = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setShowFeedback(false);
    } else {
      // Quiz complete - navigate to results
      navigate('/app/quiz/results', {
        state: {
          topic,
          difficulty,
          chapter,
          questions,
          answers: {
            ...answers,
            [currentIndex]: {
              selected: selectedAnswer,
              correct: currentQuestion.correct_answer,
              isCorrect: selectedAnswer === currentQuestion.correct_answer,
            },
          },
        },
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mb-4"></div>
          <p className="text-gray-600 text-lg">Generating questions...</p>
          <p className="text-gray-400 text-sm mt-2">This may take a moment</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-5xl mb-4">!</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to Load Quiz</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            to="/app/course"
            state={{ course: location.state?.course }}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
          >
            Back to Course
          </Link>
        </div>
      </div>
    );
  }

  // No questions state
  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 text-lg">No questions available for this chapter.</p>
          <Link
            to="/app"
            className="mt-4 inline-block px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
          >
            Back to Courses
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-xl font-bold text-blue-600">
              BeReady
            </Link>
            <Link
              to="/app/progress"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              My Progress
            </Link>
          </div>
          <span className="text-sm text-gray-500">
            {chapter.title}
          </span>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentIndex + 1} of {totalQuestions}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Question Card */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-sm p-6">
          {/* Question Type Badge */}
          <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full mb-4 ${currentQuestion.type === 'mcq'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-blue-100 text-blue-700'
            }`}>
            {currentQuestion.type === 'mcq' ? 'Multiple Choice' : 'True / False'}
          </span>

          {/* Question Text */}
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            {currentQuestion.question}
          </h2>

          {/* Answer Options */}
          <div className="space-y-3">
            {currentQuestion.type === 'mcq' ? (
              // MCQ Options
              currentQuestion.options?.map((option, idx) => {
                const optionLetter = String.fromCharCode(65 + idx); // A, B, C, D
                const isSelected = selectedAnswer === optionLetter;
                const isCorrect = optionLetter === currentQuestion.correct_answer;
                const showCorrect = showFeedback && isCorrect;
                const showIncorrect = showFeedback && isSelected && !isCorrect;

                return (
                  <button
                    key={idx}
                    onClick={() => handleAnswerSelect(optionLetter)}
                    disabled={showFeedback}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${showCorrect
                        ? 'border-green-500 bg-green-50'
                        : showIncorrect
                          ? 'border-red-500 bg-red-50'
                          : isSelected
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                      } ${showFeedback ? 'cursor-default' : 'cursor-pointer'}`}
                  >
                    <div className="flex items-start gap-3">
                      <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-medium ${showCorrect
                          ? 'bg-green-500 text-white'
                          : showIncorrect
                            ? 'bg-red-500 text-white'
                            : isSelected
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700'
                        }`}>
                        {optionLetter}
                      </span>
                      <span className="text-gray-700 pt-1">{option}</span>
                    </div>
                  </button>
                );
              })
            ) : (
              // True/False Options
              ['True', 'False'].map((option) => {
                const isSelected = selectedAnswer === option;
                const isCorrect = option === currentQuestion.correct_answer;
                const showCorrect = showFeedback && isCorrect;
                const showIncorrect = showFeedback && isSelected && !isCorrect;

                return (
                  <button
                    key={option}
                    onClick={() => handleAnswerSelect(option)}
                    disabled={showFeedback}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${showCorrect
                        ? 'border-green-500 bg-green-50'
                        : showIncorrect
                          ? 'border-red-500 bg-red-50'
                          : isSelected
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                      } ${showFeedback ? 'cursor-default' : 'cursor-pointer'}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-medium ${showCorrect
                          ? 'bg-green-500 text-white'
                          : showIncorrect
                            ? 'bg-red-500 text-white'
                            : isSelected
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700'
                        }`}>
                        {option === 'True' ? 'T' : 'F'}
                      </span>
                      <span className="text-gray-700 font-medium">{option}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Feedback / Explanation */}
          {showFeedback && currentQuestion.explanation && (
            <div className={`mt-6 p-4 rounded-lg ${answers[currentIndex]?.isCorrect || selectedAnswer === currentQuestion.correct_answer
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
              }`}>
              <p className={`font-medium mb-1 ${answers[currentIndex]?.isCorrect || selectedAnswer === currentQuestion.correct_answer
                  ? 'text-green-700'
                  : 'text-red-700'
                }`}>
                {answers[currentIndex]?.isCorrect || selectedAnswer === currentQuestion.correct_answer
                  ? 'Correct!'
                  : 'Incorrect'}
              </p>
              <p className="text-gray-600 text-sm">{currentQuestion.explanation}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 flex justify-end gap-3">
            {!showFeedback ? (
              <button
                onClick={handleSubmitAnswer}
                disabled={selectedAnswer === null}
                className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                Submit Answer
              </button>
            ) : (
              <button
                onClick={handleNextQuestion}
                className="px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors"
              >
                {currentIndex < totalQuestions - 1 ? 'Next Question' : 'See Results'}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Quiz;

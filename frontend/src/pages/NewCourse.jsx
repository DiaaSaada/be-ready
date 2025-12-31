import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { courseAPI } from '../services/api';
import Header from '../components/Header';

function NewCourse() {
  const navigate = useNavigate();

  // Form state
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('intermediate');

  // UI state
  const [isValidating, setIsValidating] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [error, setError] = useState(null);

  // Validate topic
  const handleValidate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsValidating(true);
    setError(null);
    setValidationResult(null);

    try {
      const result = await courseAPI.validate(topic);
      setValidationResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to validate topic');
    } finally {
      setIsValidating(false);
    }
  };

  // Generate course
  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const result = await courseAPI.generate(topic, difficulty);
      // Navigate to course page with the generated data
      navigate('/app/course', { state: { course: result } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate course');
      setIsGenerating(false);
    }
  };

  const isValidated = validationResult?.status === 'accepted';

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Main Content */}
      <main className="max-w-2xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Create a New Course
        </h1>
        <p className="text-gray-600 mb-8">
          Enter a topic and we'll generate a personalized course for you.
        </p>

        {/* Form */}
        <form onSubmit={handleValidate} className="space-y-6">
          {/* Topic Input */}
          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
              What do you want to learn?
            </label>
            <input
              type="text"
              id="topic"
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                setValidationResult(null);
              }}
              placeholder="e.g., Python Programming, Machine Learning, AWS Solutions Architect"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              disabled={isValidating || isGenerating}
            />
          </div>

          {/* Difficulty Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficulty Level
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {['beginner', 'intermediate', 'advanced'].map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setDifficulty(level)}
                  disabled={isValidating || isGenerating}
                  className={`py-3 px-4 rounded-lg border-2 font-medium capitalize transition-all ${
                    difficulty === level
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
            <p className="mt-2 text-sm text-gray-500">
              {difficulty === 'beginner' && 'Simple language, shorter chapters, basic concepts.'}
              {difficulty === 'intermediate' && 'Technical terms allowed, moderate depth.'}
              {difficulty === 'advanced' && 'Industry jargon, comprehensive coverage.'}
            </p>
          </div>

          {/* Validate Button */}
          {!isValidated && (
            <button
              type="submit"
              disabled={!topic.trim() || isValidating}
              className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isValidating ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Validating...
                </span>
              ) : (
                'Validate Topic'
              )}
            </button>
          )}
        </form>

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Validation Result */}
        {validationResult && (
          <div className={`mt-6 p-4 rounded-lg border ${
            validationResult.status === 'accepted'
              ? 'bg-green-50 border-green-200'
              : validationResult.status === 'needs_clarification'
              ? 'bg-yellow-50 border-yellow-200'
              : 'bg-red-50 border-red-200'
          }`}>
            {validationResult.status === 'accepted' && (
              <>
                <p className="text-green-700 font-medium mb-2">✓ Topic validated!</p>
                {validationResult.complexity && (
                  <p className="text-green-600 text-sm">
                    Complexity: {validationResult.complexity.level} •
                    Estimated chapters: {validationResult.complexity.estimated_chapters}
                  </p>
                )}
              </>
            )}
            {validationResult.status === 'needs_clarification' && (
              <>
                <p className="text-yellow-700 font-medium mb-2">⚠ Topic needs clarification</p>
                <p className="text-yellow-600 text-sm mb-2">{validationResult.message}</p>
                {validationResult.suggestions?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-yellow-700 text-sm font-medium">Suggestions:</p>
                    <ul className="list-disc list-inside text-yellow-600 text-sm">
                      {validationResult.suggestions.map((s, i) => (
                        <li key={i} className="cursor-pointer hover:underline" onClick={() => setTopic(s)}>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
            {validationResult.status === 'rejected' && (
              <>
                <p className="text-red-700 font-medium mb-2">✗ Topic rejected</p>
                <p className="text-red-600 text-sm">{validationResult.message}</p>
                {validationResult.suggestions?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-red-700 text-sm font-medium">Try instead:</p>
                    <ul className="list-disc list-inside text-red-600 text-sm">
                      {validationResult.suggestions.map((s, i) => (
                        <li key={i} className="cursor-pointer hover:underline" onClick={() => {
                          setTopic(s);
                          setValidationResult(null);
                        }}>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Generate Button */}
        {isValidated && (
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="mt-6 w-full py-4 px-4 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-lg"
          >
            {isGenerating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating Course...
              </span>
            ) : (
              '🚀 Generate Course'
            )}
          </button>
        )}
      </main>
    </div>
  );
}

export default NewCourse;

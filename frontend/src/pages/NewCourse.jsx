import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { courseAPI } from '../services/api';
import Header from '../components/Header';
import FileUpload from '../components/FileUpload';
import DocumentOutlineReview from '../components/DocumentOutlineReview';

function NewCourse() {
  const navigate = useNavigate();

  // Mode: 'topic' or 'files'
  const [mode, setMode] = useState('topic');

  // Common state
  const [difficulty, setDifficulty] = useState('intermediate');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Topic mode state
  const [topic, setTopic] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  // Files mode state
  const [files, setFiles] = useState([]);
  const [optionalTopic, setOptionalTopic] = useState('');

  // Two-phase file flow state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Reset state when switching modes
  const handleModeChange = (newMode) => {
    setMode(newMode);
    setError(null);
    setSuccessMessage(null);
    setValidationResult(null);
    setAnalysisResult(null);
  };

  // Validate topic (topic mode)
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

  // Generate course from topic
  const handleGenerateFromTopic = async () => {
    setIsGenerating(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await courseAPI.generate(topic, difficulty);
      setSuccessMessage(`Course "${result.topic}" created successfully!`);
      setIsGenerating(false);

      setTimeout(() => {
        navigate('/app/my-courses');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate course');
      setIsGenerating(false);
    }
  };

  // Phase 1: Analyze files to detect document structure
  const handleAnalyzeFiles = async () => {
    if (files.length === 0) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await courseAPI.analyzeFiles(files);
      setAnalysisResult(result);
      setIsAnalyzing(false);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object') {
        setError(detail.message || JSON.stringify(detail));
      } else {
        setError(detail || 'Failed to analyze files');
      }
      setIsAnalyzing(false);
    }
  };

  // Phase 2: Generate course from confirmed outline
  const handleConfirmOutline = async (confirmedSections, customTopic) => {
    setIsGenerating(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await courseAPI.generateFromOutline(
        analysisResult.analysis_id,
        confirmedSections,
        difficulty,
        customTopic
      );

      // Show results including any file processing errors
      const successCount = result.source_files?.filter((f) => f.success).length || 0;
      const failCount = result.source_files?.filter((f) => !f.success).length || 0;

      let message = `Course "${result.topic}" created with ${result.total_chapters} chapters!`;
      if (failCount > 0) {
        message += ` (${failCount} file(s) could not be processed)`;
      }

      setSuccessMessage(message);
      setIsGenerating(false);

      setTimeout(() => {
        navigate('/app/my-courses');
      }, 2000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object') {
        setError(detail.message || JSON.stringify(detail));
      } else {
        setError(detail || 'Failed to generate course');
      }
      setIsGenerating(false);
    }
  };

  // Cancel outline review and go back to file selection
  const handleCancelOutline = () => {
    setAnalysisResult(null);
    setError(null);
  };

  // Legacy: Generate course from files directly (single phase)
  const handleGenerateFromFiles = async () => {
    if (files.length === 0) return;

    setIsGenerating(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await courseAPI.generateFromFiles(
        files,
        optionalTopic || null,
        difficulty
      );

      // Show results including any file processing errors
      const successCount = result.source_files.filter((f) => f.success).length;
      const failCount = result.source_files.filter((f) => !f.success).length;

      let message = `Course "${result.topic}" created from ${successCount} file(s)!`;
      if (failCount > 0) {
        message += ` (${failCount} file(s) could not be processed)`;
      }

      setSuccessMessage(message);
      setIsGenerating(false);

      setTimeout(() => {
        navigate('/app/my-courses');
      }, 2000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object') {
        setError(detail.message || JSON.stringify(detail));
      } else {
        setError(detail || 'Failed to generate course from files');
      }
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
          Generate a personalized course from a topic or your own study materials.
        </p>

        {/* Mode Toggle */}
        <div className="flex gap-2 mb-8">
          <button
            onClick={() => handleModeChange('topic')}
            disabled={isGenerating}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              mode === 'topic'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            From Topic
          </button>
          <button
            onClick={() => handleModeChange('files')}
            disabled={isGenerating}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              mode === 'files'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            From Files
          </button>
        </div>

        {/* Topic Mode */}
        {mode === 'topic' && (
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

            {/* Validation Result */}
            {validationResult && (
              <div className={`p-4 rounded-lg border ${
                validationResult.status === 'accepted'
                  ? 'bg-green-50 border-green-200'
                  : validationResult.status === 'needs_clarification'
                  ? 'bg-yellow-50 border-yellow-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                {validationResult.status === 'accepted' && (
                  <>
                    <p className="text-green-700 font-medium mb-2">Topic validated!</p>
                    {validationResult.complexity && (
                      <p className="text-green-600 text-sm">
                        Complexity: {validationResult.complexity.level} |
                        Estimated chapters: {validationResult.complexity.estimated_chapters}
                      </p>
                    )}
                  </>
                )}
                {validationResult.status === 'needs_clarification' && (
                  <>
                    <p className="text-yellow-700 font-medium mb-2">Topic needs clarification</p>
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
                    <p className="text-red-700 font-medium mb-2">Topic rejected</p>
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

            {/* Generate Button (Topic Mode) */}
            {isValidated && !successMessage && (
              <button
                type="button"
                onClick={handleGenerateFromTopic}
                disabled={isGenerating}
                className="w-full py-4 px-4 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-lg"
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
                  'Generate Course'
                )}
              </button>
            )}
          </form>
        )}

        {/* Files Mode */}
        {mode === 'files' && (
          <div className="space-y-6">
            {/* Phase 1: File Upload (before analysis) */}
            {!analysisResult && (
              <>
                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload Your Study Materials
                  </label>
                  <FileUpload onFilesChange={setFiles} disabled={isAnalyzing} />
                </div>

                {/* Analyze Button */}
                <button
                  onClick={handleAnalyzeFiles}
                  disabled={files.length === 0 || isAnalyzing}
                  className="w-full py-4 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-lg"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Analyzing Document Structure...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      Analyze {files.length} File{files.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </button>

                <p className="text-sm text-gray-500 text-center">
                  We'll analyze your files and show you the detected sections before generating the course.
                </p>
              </>
            )}

            {/* Phase 2: Outline Review (after analysis) */}
            {analysisResult && !successMessage && (
              <DocumentOutlineReview
                analysisResult={analysisResult}
                onConfirm={handleConfirmOutline}
                onCancel={handleCancelOutline}
                isGenerating={isGenerating}
                difficulty={difficulty}
                setDifficulty={setDifficulty}
              />
            )}
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <p className="text-green-700 font-medium">{successMessage}</p>
                <p className="text-green-600 text-sm">Redirecting to My Courses...</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default NewCourse;

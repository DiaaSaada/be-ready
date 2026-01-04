import { useState } from 'react';

function DocumentOutlineReview({
  analysisResult,
  onConfirm,
  onCancel,
  isGenerating,
  difficulty,
  setDifficulty
}) {
  const { document_outline } = analysisResult;

  // Initialize sections state with include=true and editable titles/topics
  const [sections, setSections] = useState(
    document_outline.sections.map((section) => ({
      order: section.order,
      title: section.title,
      include: true,
      key_topics: [...section.key_topics],
      summary: section.summary,
      confidence: section.confidence,
      source_file: section.source_file,
    }))
  );

  const [customTopic, setCustomTopic] = useState('');
  const [newTopicInputs, setNewTopicInputs] = useState({});

  const toggleSection = (order) => {
    setSections((prev) =>
      prev.map((s) =>
        s.order === order ? { ...s, include: !s.include } : s
      )
    );
  };

  const updateSectionTitle = (order, newTitle) => {
    setSections((prev) =>
      prev.map((s) =>
        s.order === order ? { ...s, title: newTitle } : s
      )
    );
  };

  const removeTopic = (order, topicIndex) => {
    setSections((prev) =>
      prev.map((s) =>
        s.order === order
          ? { ...s, key_topics: s.key_topics.filter((_, i) => i !== topicIndex) }
          : s
      )
    );
  };

  const addTopic = (order) => {
    const newTopic = newTopicInputs[order]?.trim();
    if (!newTopic) return;

    setSections((prev) =>
      prev.map((s) =>
        s.order === order
          ? { ...s, key_topics: [...s.key_topics, newTopic] }
          : s
      )
    );
    setNewTopicInputs((prev) => ({ ...prev, [order]: '' }));
  };

  const handleConfirm = () => {
    const confirmedSections = sections
      .filter((s) => s.include)
      .map((s) => ({
        order: s.order,
        title: s.title,
        include: true,
        key_topics: s.key_topics,
      }));

    onConfirm(confirmedSections, customTopic || null);
  };

  const includedCount = sections.filter((s) => s.include).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div>
            <h3 className="font-semibold text-blue-900">
              {document_outline.document_title}
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              Detected {document_outline.total_sections} sections from your {document_outline.document_type}
            </p>
            {document_outline.analysis_notes && (
              <p className="text-xs text-blue-600 mt-1 italic">
                {document_outline.analysis_notes}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Instructions */}
      <p className="text-gray-600 text-sm">
        Review the detected sections below. You can exclude sections, edit titles, and modify topics.
        Each section will become a chapter in your course.
      </p>

      {/* Sections List */}
      <div className="space-y-3">
        {sections.map((section) => (
          <div
            key={section.order}
            className={`border rounded-lg p-4 transition-all ${
              section.include
                ? 'border-green-300 bg-white'
                : 'border-gray-200 bg-gray-50 opacity-60'
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Checkbox */}
              <button
                onClick={() => toggleSection(section.order)}
                disabled={isGenerating}
                className={`w-6 h-6 rounded border-2 flex items-center justify-center flex-shrink-0 mt-1 transition-colors ${
                  section.include
                    ? 'bg-green-500 border-green-500 text-white'
                    : 'border-gray-300 bg-white'
                }`}
              >
                {section.include && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>

              {/* Content */}
              <div className="flex-1 min-w-0">
                {/* Chapter number and editable title */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-500">
                    Chapter {section.order}:
                  </span>
                  <input
                    type="text"
                    value={section.title}
                    onChange={(e) => updateSectionTitle(section.order, e.target.value)}
                    disabled={isGenerating || !section.include}
                    className={`flex-1 font-semibold text-gray-900 bg-transparent border-b border-transparent
                      focus:border-blue-500 focus:outline-none transition-colors
                      ${section.include ? '' : 'text-gray-500'}`}
                  />
                  {section.confidence && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      section.confidence >= 0.8
                        ? 'bg-green-100 text-green-700'
                        : section.confidence >= 0.5
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {Math.round(section.confidence * 100)}% match
                    </span>
                  )}
                  {section.source_file && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {section.source_file}
                    </span>
                  )}
                </div>

                {/* Summary */}
                <p className="text-sm text-gray-600 mb-3">{section.summary}</p>

                {/* Topics as chips */}
                <div className="flex flex-wrap gap-2">
                  {section.key_topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                        section.include
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {topic}
                      {section.include && (
                        <button
                          onClick={() => removeTopic(section.order, idx)}
                          disabled={isGenerating}
                          className="hover:text-red-600 ml-1"
                          title="Remove topic"
                        >
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </span>
                  ))}

                  {/* Add topic input */}
                  {section.include && (
                    <div className="inline-flex items-center gap-1">
                      <input
                        type="text"
                        placeholder="Add topic..."
                        value={newTopicInputs[section.order] || ''}
                        onChange={(e) =>
                          setNewTopicInputs((prev) => ({
                            ...prev,
                            [section.order]: e.target.value,
                          }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            addTopic(section.order);
                          }
                        }}
                        disabled={isGenerating}
                        className="w-24 px-2 py-1 text-xs border border-gray-300 rounded-full focus:border-blue-500 focus:outline-none"
                      />
                      <button
                        onClick={() => addTopic(section.order)}
                        disabled={isGenerating || !newTopicInputs[section.order]?.trim()}
                        className="p-1 text-blue-600 hover:text-blue-800 disabled:text-gray-400"
                        title="Add topic"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Custom Topic Override */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Course Title (optional)
        </label>
        <input
          type="text"
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          placeholder={document_outline.document_title}
          disabled={isGenerating}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
        />
        <p className="text-xs text-gray-500 mt-1">
          Leave blank to use detected title: "{document_outline.document_title}"
        </p>
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
              disabled={isGenerating}
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

      {/* Summary */}
      <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between">
        <div>
          <p className="text-gray-700">
            <span className="font-semibold">{includedCount}</span> of {sections.length} sections selected
          </p>
          <p className="text-sm text-gray-500">
            Estimated time: ~{document_outline.estimated_total_time_minutes} minutes
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onCancel}
          disabled={isGenerating}
          className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={isGenerating || includedCount === 0}
          className="flex-1 py-3 px-4 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
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
            `Generate Course (${includedCount} chapters)`
          )}
        </button>
      </div>
    </div>
  );
}

export default DocumentOutlineReview;

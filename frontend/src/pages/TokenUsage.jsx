import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { tokenAPI } from '../services/api';
import Header from '../components/Header';

function TokenUsage() {
  const [usage, setUsage] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 20;

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [usageData, summaryData] = await Promise.all([
          tokenAPI.getUsage(limit, 0),
          tokenAPI.getSummary(),
        ]);

        setUsage(usageData.records || []);
        setSummary(summaryData);
        setHasMore((usageData.records || []).length === limit);
      } catch (err) {
        console.error('Failed to load token usage:', err);
        setError('Failed to load token usage data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const loadMore = async () => {
    try {
      const newOffset = offset + limit;
      const usageData = await tokenAPI.getUsage(limit, newOffset);
      const newRecords = usageData.records || [];

      setUsage((prev) => [...prev, ...newRecords]);
      setOffset(newOffset);
      setHasMore(newRecords.length === limit);
    } catch (err) {
      console.error('Failed to load more:', err);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num?.toLocaleString() || '0';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getOperationLabel = (op) => {
    const labels = {
      ANALYZE_DOCUMENT: 'Document Analysis',
      CHAPTER_GENERATION: 'Chapter Generation',
      QUESTION_GENERATION: 'Question Generation',
      ANSWER_CHECK: 'Answer Check',
      FEEDBACK_GENERATION: 'Feedback',
      RAG_ANSWER: 'Q&A',
    };
    return labels[op] || op;
  };

  const getOperationColor = (op) => {
    const colors = {
      ANALYZE_DOCUMENT: 'bg-purple-100 text-purple-700',
      CHAPTER_GENERATION: 'bg-blue-100 text-blue-700',
      QUESTION_GENERATION: 'bg-green-100 text-green-700',
      ANSWER_CHECK: 'bg-yellow-100 text-yellow-700',
      FEEDBACK_GENERATION: 'bg-orange-100 text-orange-700',
      RAG_ANSWER: 'bg-pink-100 text-pink-700',
    };
    return colors[op] || 'bg-gray-100 text-gray-700';
  };

  const getProviderColor = (provider) => {
    const colors = {
      claude: 'bg-orange-100 text-orange-700',
      openai: 'bg-emerald-100 text-emerald-700',
      gemini: 'bg-blue-100 text-blue-700',
      mock: 'bg-gray-100 text-gray-600',
    };
    return colors[provider?.toLowerCase()] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Token Usage</h1>
        <p className="text-gray-600 mb-8">Track your AI token consumption across all operations</p>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-4"></div>
            <p className="text-gray-600">Loading usage data...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        {!isLoading && summary && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-blue-600">{formatNumber(summary.total_tokens)}</p>
                <p className="text-sm text-gray-600">Total Tokens</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-green-600">{formatNumber(summary.total_input_tokens)}</p>
                <p className="text-sm text-gray-600">Input Tokens</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-purple-600">{formatNumber(summary.total_output_tokens)}</p>
                <p className="text-sm text-gray-600">Output Tokens</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-3xl font-bold text-orange-600">{summary.record_count}</p>
                <p className="text-sm text-gray-600">API Calls</p>
              </div>
            </div>

            {/* By Provider */}
            {summary.by_provider && Object.keys(summary.by_provider).length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">By Provider</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(summary.by_provider).map(([provider, tokens]) => (
                    <span key={provider} className={`px-3 py-1 rounded-full text-sm font-medium ${getProviderColor(provider)}`}>
                      {provider}: {formatNumber(tokens)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* By Operation */}
            {summary.by_operation && Object.keys(summary.by_operation).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">By Operation</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(summary.by_operation).map(([op, tokens]) => (
                    <span key={op} className={`px-3 py-1 rounded-full text-sm font-medium ${getOperationColor(op)}`}>
                      {getOperationLabel(op)}: {formatNumber(tokens)}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && usage.length === 0 && (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm">
            <div className="text-5xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No token usage yet</h2>
            <p className="text-gray-600 mb-6">Generate some courses or questions to see your token usage</p>
            <Link
              to="/app"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
            >
              Create a Course
            </Link>
          </div>
        )}

        {/* Usage History Table */}
        {!isLoading && usage.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Usage History</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Operation</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Provider</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Context</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Input</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Output</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {usage.map((record, idx) => (
                    <tr key={`${record.created_at}-${idx}`} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(record.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getOperationColor(record.operation)}`}>
                          {getOperationLabel(record.operation)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getProviderColor(record.provider)}`}>
                          {record.provider}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate" title={record.context}>
                        {record.context || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                        {record.input_tokens?.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-mono">
                        {record.output_tokens?.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 text-right font-mono">
                        {record.total_tokens?.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="px-6 py-4 border-t border-gray-200 text-center">
                <button
                  onClick={loadMore}
                  className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  Load More
                </button>
              </div>
            )}
          </div>
        )}

        {/* Back Button */}
        {!isLoading && usage.length > 0 && (
          <div className="mt-8 text-center">
            <Link
              to="/app/my-courses"
              className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200"
            >
              Back to My Courses
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}

export default TokenUsage;

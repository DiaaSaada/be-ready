import axios from 'axios';

// API base URL - in dev, Vite proxy will handle this (use empty string for relative URLs)
// In production, set VITE_API_URL to the backend URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Course endpoints
export const courseAPI = {
  // Validate a topic before generating
  validate: async (topic) => {
    const response = await api.post('/api/v1/courses/validate', { topic });
    return response.data;
  },

  // Generate chapters for a course
  generate: async (topic, difficulty, skipValidation = false) => {
    const response = await api.post('/api/v1/courses/generate', {
      topic,
      difficulty,
      skip_validation: skipValidation,
    });
    return response.data;
  },

  // Get user's created courses
  getMyCourses: async () => {
    const response = await api.get('/api/v1/courses/my-courses');
    return response.data;
  },

  // Get a single course by ID
  getById: async (courseId) => {
    const response = await api.get(`/api/v1/courses/${courseId}`);
    return response.data;
  },

  // Delete a course
  deleteCourse: async (courseId) => {
    const response = await api.delete(`/api/v1/courses/${courseId}`);
    return response.data;
  },

  // Get available providers
  getProviders: async () => {
    const response = await api.get('/api/v1/courses/providers');
    return response.data;
  },

  // Get difficulty presets
  getPresets: async () => {
    const response = await api.get('/api/v1/courses/config-presets');
    return response.data;
  },

  // Generate course from uploaded files (legacy - direct generation)
  generateFromFiles: async (files, topic = null, difficulty = 'intermediate') => {
    const formData = new FormData();

    // Append each file
    files.forEach((file) => {
      formData.append('files', file);
    });

    // Append form fields
    if (topic) {
      formData.append('topic', topic);
    }
    formData.append('difficulty', difficulty);

    const response = await api.post('/api/v1/courses/generate-from-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minute timeout for file processing
    });
    return response.data;
  },

  // Phase 1: Analyze files and detect document structure
  analyzeFiles: async (files) => {
    const formData = new FormData();

    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post('/api/v1/courses/analyze-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 1 minute timeout for analysis
    });
    return response.data;
  },

  // Phase 2: Generate course from confirmed outline
  generateFromOutline: async (analysisId, confirmedSections, difficulty, customTopic = null) => {
    const response = await api.post('/api/v1/courses/generate-from-outline', {
      analysis_id: analysisId,
      confirmed_sections: confirmedSections,
      difficulty,
      custom_topic: customTopic,
    }, {
      timeout: 120000, // 2 minute timeout for generation
    });
    return response.data;
  },
};

// Question endpoints
export const questionAPI = {
  // Generate questions for a chapter
  generate: async (topic, difficulty, chapterNumber, chapterTitle, keyConcepts, chunked = true) => {
    const response = await api.post('/api/v1/questions/generate', {
      topic,
      difficulty,
      chapter_number: chapterNumber,
      chapter_title: chapterTitle,
      key_concepts: keyConcepts,
    }, {
      params: { chunked },
    });
    return response.data;
  },

  // Get sample questions (for testing)
  getSample: async (topic, difficulty) => {
    const response = await api.get('/api/v1/questions/sample', {
      params: { topic, difficulty },
    });
    return response.data;
  },

  // Get question counts for all chapters of a course
  getCounts: async (topic, difficulty) => {
    const response = await api.get('/api/v1/questions/counts', {
      params: { topic, difficulty },
    });
    return response.data;
  },
};

// Progress endpoints
export const progressAPI = {
  // Submit quiz results
  submit: async (userId, data) => {
    const response = await api.post('/api/v1/progress/submit', {
      user_id: userId,
      topic: data.topic,
      difficulty: data.difficulty,
      chapter_number: data.chapterNumber,
      chapter_title: data.chapterTitle,
      answers: data.answers,
      total_questions: data.totalQuestions,
      correct_count: data.correctCount,
    });
    return response.data;
  },

  // Get all progress for a user
  getAll: async (userId) => {
    const response = await api.get(`/api/v1/progress/${userId}`);
    return response.data;
  },

  // Get progress for a specific course (by topic and difficulty)
  getCourse: async (userId, topic, difficulty) => {
    const response = await api.get(`/api/v1/progress/${userId}`, {
      params: { topic: topic.toLowerCase(), difficulty },
    });
    return response.data;
  },

  // Get user summary
  getSummary: async (userId) => {
    const response = await api.get(`/api/v1/progress/${userId}/summary`);
    return response.data;
  },

  // Delete progress (for retry)
  delete: async (userId, topic, chapterNumber) => {
    const response = await api.delete(`/api/v1/progress/${userId}/${topic}/${chapterNumber}`);
    return response.data;
  },
};

// Token usage endpoints
export const tokenAPI = {
  // Get paginated token usage history
  getUsage: async (limit = 50, offset = 0) => {
    const response = await api.get('/api/v1/tokens/usage', {
      params: { limit, offset },
    });
    return response.data;
  },

  // Get aggregated token usage summary
  getSummary: async () => {
    const response = await api.get('/api/v1/tokens/usage/summary');
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Response interceptor to handle 401 errors (token expired/invalid)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stored auth data
      localStorage.removeItem('beready_token');
      localStorage.removeItem('beready_user');
      delete api.defaults.headers.common['Authorization'];

      // Redirect to login if not already there
      if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

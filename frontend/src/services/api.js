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

  // Get progress for a specific course
  getCourse: async (userId, topic) => {
    const response = await api.get(`/api/v1/progress/${userId}`, {
      params: { topic },
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

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;

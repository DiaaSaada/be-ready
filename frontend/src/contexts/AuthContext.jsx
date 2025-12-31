import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

const TOKEN_KEY = 'beready_token';
const USER_KEY = 'beready_user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      // Set default auth header
      api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
    }

    setIsLoading(false);
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/api/v1/auth/login', { email, password });
    const { access_token } = response.data;

    // Set token in axios headers
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    // Fetch user info
    const userResponse = await api.get('/api/v1/auth/me');
    const userData = userResponse.data;

    // Store in state and localStorage
    setToken(access_token);
    setUser(userData);
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));

    return userData;
  };

  const signup = async (name, email, password) => {
    const response = await api.post('/api/v1/auth/signup', {
      name,
      email,
      password
    });
    const { access_token } = response.data;

    // Set token in axios headers
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    // Fetch user info
    const userResponse = await api.get('/api/v1/auth/me');
    const userData = userResponse.data;

    // Store in state and localStorage
    setToken(access_token);
    setUser(userData);
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));

    return userData;
  };

  const logout = () => {
    // Clear state
    setToken(null);
    setUser(null);

    // Clear localStorage
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    // Clear axios header
    delete api.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    signup,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

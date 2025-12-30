import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL;

export const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Dev logging: show outgoing request details to help debug backend 4xx/5xx
  if (import.meta.env.DEV) {
    try {
      // Clone config data safely for logging
      const safeData = config.data ? JSON.parse(JSON.stringify(config.data)) : undefined;
      // eslint-disable-next-line no-console
      console.debug('[api] Request:', config.method?.toUpperCase(), config.url, safeData);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.debug('[api] Request (unserializable):', config.method?.toUpperCase(), config.url);
    }
  }
  return config;
});

// Add response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Dev: log error response body for easier debugging
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error('[api] Response error:', error.response?.status, error.response?.data || error.message);
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);
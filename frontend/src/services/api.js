import axios from 'axios';
import { logError, logInfo } from '../utils/logger';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('backend_access_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    logInfo('API request:', {
      method: config.method,
      url: `${config.baseURL}${config.url}`,
      data: config.data,
      params: config.params,
    });

    return config;
  },
  (error) => {
    logError('API request error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    logInfo('API response:', {
      status: response.status,
      url: response.config?.url,
      data: response.data,
    });
    return response;
  },
  (error) => {
    logError('API error:', {
      message: error.message,
      status: error.response?.status,
      url: error.config?.url,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

export default api;

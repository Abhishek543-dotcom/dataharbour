import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token and redirect to login
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getTrends: () => api.get('/dashboard/trends'),
  getOverview: () => api.get('/dashboard/overview'),
};

// Jobs API
export const jobsAPI = {
  getAll: (params) => api.get('/jobs/', { params }),
  getById: (id) => api.get(`/jobs/${id}`),
  create: (data) => api.post('/jobs/', data),
  kill: (id) => api.post(`/jobs/${id}/kill`),
  restart: (id) => api.post(`/jobs/${id}/restart`),
  getLogs: (id) => api.get(`/jobs/${id}/logs`),
  getSparkUI: (id) => api.get(`/jobs/${id}/spark-ui`),
};

// Clusters API
export const clustersAPI = {
  getAll: () => api.get('/clusters/'),
  getById: (id) => api.get(`/clusters/${id}`),
  create: (data) => api.post('/clusters/', data),
  delete: (id) => api.delete(`/clusters/${id}`),
};

// Monitoring API
export const monitoringAPI = {
  getMetrics: () => api.get('/monitoring/metrics'),
  getMetricsHistory: (hours = 24) => api.get('/monitoring/metrics/history', { params: { hours } }),
  getServices: () => api.get('/monitoring/services'),
  getServiceLogs: (serviceName, lines = 100) => api.get(`/monitoring/services/${serviceName}/logs`, { params: { lines } }),
  getOverview: () => api.get('/monitoring/overview'),
};

// Database API
export const databaseAPI = {
  getDatabases: () => api.get('/database/databases'),
  getTables: (database) => api.get(`/database/databases/${database}/tables`),
  getTableSchema: (database, schema, table) => api.get(`/database/databases/${database}/tables/${schema}/${table}/schema`),
  previewTable: (database, schema, table, params) => api.get(`/database/databases/${database}/tables/${schema}/${table}/preview`, { params }),
  executeQuery: (database, query, limit = 1000) => api.post(`/database/databases/${database}/query`, { query, limit }),
};

export { api };
export default api;

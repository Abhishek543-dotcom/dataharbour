import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token (when implemented)
api.interceptors.request.use(
  (config) => {
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
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
      // Handle unauthorized - redirect to login when auth is implemented
      console.error('Unauthorized access');
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

// Notebooks API
export const notebooksAPI = {
  getAll: () => api.get('/notebooks/'),
  getById: (id) => api.get(`/notebooks/${id}`),
  create: (data) => api.post('/notebooks/', data),
  update: (id, data) => api.put(`/notebooks/${id}`, data),
  delete: (id) => api.delete(`/notebooks/${id}`),
  addCell: (id, cell) => api.post(`/notebooks/${id}/cells`, cell),
  deleteCell: (id, cellId) => api.delete(`/notebooks/${id}/cells/${cellId}`),
  executeCell: (id, cellId, code) => api.post(`/notebooks/${id}/cells/${cellId}/execute`, { code }),
  import: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/notebooks/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  export: (id) => api.get(`/notebooks/${id}/export`),
};

// Monitoring API
export const monitoringAPI = {
  getMetrics: () => api.get('/monitoring/metrics'),
  getMetricsHistory: (hours = 24) => api.get('/monitoring/metrics/history', { params: { hours } }),
  getServices: () => api.get('/monitoring/services'),
  getServiceLogs: (serviceName, lines = 100) => api.get(`/monitoring/services/${serviceName}/logs`, { params: { lines } }),
  getOverview: () => api.get('/monitoring/overview'),
};

export default api;

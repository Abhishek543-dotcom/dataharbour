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

// Database API
export const databaseAPI = {
  getDatabases: () => api.get('/database/databases'),
  getTables: (database) => api.get(`/database/databases/${database}/tables`),
  getTableSchema: (database, schema, table) => api.get(`/database/databases/${database}/tables/${schema}/${table}/schema`),
  previewTable: (database, schema, table, params) => api.get(`/database/databases/${database}/tables/${schema}/${table}/preview`, { params }),
  executeQuery: (database, query, limit = 1000) => api.post(`/database/databases/${database}/query`, { query, limit }),
};

// Airflow API
export const airflowAPI = {
  getHealth: () => api.get('/airflow/health'),
  getStatistics: () => api.get('/airflow/statistics'),
  getDags: (params) => api.get('/airflow/dags', { params }),
  getDag: (dagId) => api.get(`/airflow/dags/${dagId}`),
  getDagRuns: (dagId, params) => api.get(`/airflow/dags/${dagId}/runs`, { params }),
  triggerDag: (dagId, conf = {}) => api.post(`/airflow/dags/${dagId}/trigger`, { conf }),
  pauseDag: (dagId) => api.post(`/airflow/dags/${dagId}/pause`),
  unpauseDag: (dagId) => api.post(`/airflow/dags/${dagId}/unpause`),
  getTaskInstances: (dagId, dagRunId) => api.get(`/airflow/dags/${dagId}/runs/${dagRunId}/tasks`),
  getTaskLogs: (dagId, dagRunId, taskId, tryNumber = 1) => api.get(`/airflow/dags/${dagId}/runs/${dagRunId}/tasks/${taskId}/logs`, { params: { try_number: tryNumber } }),
};

// Storage API
export const storageAPI = {
  getBuckets: () => api.get('/storage/buckets'),
  createBucket: (bucketName) => api.post('/storage/buckets', { bucket_name: bucketName }),
  deleteBucket: (bucketName) => api.delete(`/storage/buckets/${bucketName}`),
  getBucketStats: (bucketName) => api.get(`/storage/buckets/${bucketName}/stats`),
  listObjects: (bucketName, params) => api.get(`/storage/buckets/${bucketName}/objects`, { params }),
  getObjectInfo: (bucketName, objectPath) => api.get(`/storage/buckets/${bucketName}/objects/${objectPath}/info`),
  getObjectUrl: (bucketName, objectPath, expiry = 3600) => api.get(`/storage/buckets/${bucketName}/objects/${objectPath}/url`, { params: { expiry } }),
  uploadObject: (bucketName, objectPath, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/storage/buckets/${bucketName}/objects/${objectPath}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  downloadObject: (bucketName, objectPath) => api.get(`/storage/buckets/${bucketName}/objects/${objectPath}/download`, { responseType: 'blob' }),
  deleteObject: (bucketName, objectPath) => api.delete(`/storage/buckets/${bucketName}/objects/${objectPath}`),
  copyObject: (sourceBucket, sourceObject, destBucket, destObject) => api.post('/storage/objects/copy', {
    source_bucket: sourceBucket,
    source_object: sourceObject,
    dest_bucket: destBucket,
    dest_object: destObject,
  }),
};

export { api };
export default api;

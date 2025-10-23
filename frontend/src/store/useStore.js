import { create } from 'zustand';
import { dashboardAPI, jobsAPI, clustersAPI, notebooksAPI, monitoringAPI } from '../services/api';

const useStore = create((set, get) => ({
  // Dashboard state
  dashboardStats: null,
  dashboardTrends: null,
  loadingDashboard: false,

  // Jobs state
  jobs: [],
  selectedJob: null,
  loadingJobs: false,
  jobFilter: {
    status: null,
    cluster: null,
    search: '',
  },

  // Clusters state
  clusters: [],
  selectedCluster: null,
  loadingClusters: false,

  // Notebooks state
  notebooks: [],
  selectedNotebook: null,
  loadingNotebooks: false,

  // Monitoring state
  metrics: null,
  services: [],
  loadingMonitoring: false,

  // WebSocket connection status
  wsConnected: false,

  // Actions - Dashboard
  fetchDashboardData: async () => {
    set({ loadingDashboard: true });
    try {
      const [statsRes, trendsRes] = await Promise.all([
        dashboardAPI.getStats(),
        dashboardAPI.getTrends(),
      ]);
      set({
        dashboardStats: statsRes.data,
        dashboardTrends: trendsRes.data,
        loadingDashboard: false,
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      set({ loadingDashboard: false });
    }
  },

  // Actions - Jobs
  fetchJobs: async (filters = {}) => {
    set({ loadingJobs: true });
    try {
      const response = await jobsAPI.getAll(filters);
      set({ jobs: response.data, loadingJobs: false });
    } catch (error) {
      console.error('Error fetching jobs:', error);
      set({ loadingJobs: false });
    }
  },

  fetchJobDetails: async (jobId) => {
    try {
      const response = await jobsAPI.getById(jobId);
      set({ selectedJob: response.data });
    } catch (error) {
      console.error('Error fetching job details:', error);
    }
  },

  createJob: async (jobData) => {
    try {
      const response = await jobsAPI.create(jobData);
      const { jobs } = get();
      set({ jobs: [response.data, ...jobs] });
      return response.data;
    } catch (error) {
      console.error('Error creating job:', error);
      throw error;
    }
  },

  killJob: async (jobId) => {
    try {
      await jobsAPI.kill(jobId);
      get().fetchJobs();
    } catch (error) {
      console.error('Error killing job:', error);
      throw error;
    }
  },

  restartJob: async (jobId) => {
    try {
      const response = await jobsAPI.restart(jobId);
      get().fetchJobs();
      return response.data;
    } catch (error) {
      console.error('Error restarting job:', error);
      throw error;
    }
  },

  updateJobFilter: (filter) => {
    set({ jobFilter: { ...get().jobFilter, ...filter } });
  },

  updateJobInList: (jobData) => {
    const { jobs } = get();
    const index = jobs.findIndex(j => j.id === jobData.job_id || j.id === jobData.id);
    if (index !== -1) {
      const updatedJobs = [...jobs];
      updatedJobs[index] = { ...updatedJobs[index], ...jobData };
      set({ jobs: updatedJobs });
    }
  },

  // Actions - Clusters
  fetchClusters: async () => {
    set({ loadingClusters: true });
    try {
      const response = await clustersAPI.getAll();
      set({ clusters: response.data, loadingClusters: false });
    } catch (error) {
      console.error('Error fetching clusters:', error);
      set({ loadingClusters: false });
    }
  },

  createCluster: async (clusterData) => {
    try {
      const response = await clustersAPI.create(clusterData);
      const { clusters } = get();
      set({ clusters: [...clusters, response.data] });
      return response.data;
    } catch (error) {
      console.error('Error creating cluster:', error);
      throw error;
    }
  },

  deleteCluster: async (clusterId) => {
    try {
      await clustersAPI.delete(clusterId);
      const { clusters } = get();
      set({ clusters: clusters.filter(c => c.id !== clusterId) });
    } catch (error) {
      console.error('Error deleting cluster:', error);
      throw error;
    }
  },

  // Actions - Notebooks
  fetchNotebooks: async () => {
    set({ loadingNotebooks: true });
    try {
      const response = await notebooksAPI.getAll();
      set({ notebooks: response.data, loadingNotebooks: false });
    } catch (error) {
      console.error('Error fetching notebooks:', error);
      set({ loadingNotebooks: false });
    }
  },

  fetchNotebookDetails: async (notebookId) => {
    try {
      const response = await notebooksAPI.getById(notebookId);
      set({ selectedNotebook: response.data });
    } catch (error) {
      console.error('Error fetching notebook details:', error);
    }
  },

  createNotebook: async (notebookData) => {
    try {
      const response = await notebooksAPI.create(notebookData);
      const { notebooks } = get();
      set({ notebooks: [response.data, ...notebooks] });
      return response.data;
    } catch (error) {
      console.error('Error creating notebook:', error);
      throw error;
    }
  },

  updateNotebook: async (notebookId, data) => {
    try {
      const response = await notebooksAPI.update(notebookId, data);
      set({ selectedNotebook: response.data });
      get().fetchNotebooks();
    } catch (error) {
      console.error('Error updating notebook:', error);
      throw error;
    }
  },

  deleteNotebook: async (notebookId) => {
    try {
      await notebooksAPI.delete(notebookId);
      const { notebooks } = get();
      set({ notebooks: notebooks.filter(n => n.id !== notebookId) });
    } catch (error) {
      console.error('Error deleting notebook:', error);
      throw error;
    }
  },

  executeCell: async (notebookId, cellId, code) => {
    try {
      const response = await notebooksAPI.executeCell(notebookId, cellId, code);
      return response.data;
    } catch (error) {
      console.error('Error executing cell:', error);
      throw error;
    }
  },

  // Actions - Monitoring
  fetchMonitoring: async () => {
    set({ loadingMonitoring: true });
    try {
      const [metricsRes, servicesRes] = await Promise.all([
        monitoringAPI.getMetrics(),
        monitoringAPI.getServices(),
      ]);
      set({
        metrics: metricsRes.data,
        services: servicesRes.data,
        loadingMonitoring: false,
      });
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      set({ loadingMonitoring: false });
    }
  },

  updateMetrics: (metricsData) => {
    set({ metrics: metricsData });
  },

  // WebSocket
  setWsConnected: (connected) => {
    set({ wsConnected: connected });
  },
}));

export default useStore;

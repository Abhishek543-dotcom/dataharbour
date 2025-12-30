import { useState, useEffect } from 'react';
import { Server, Plus, ExternalLink, Trash2, RefreshCw, Activity, Cpu, HardDrive, Clock, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import { clustersAPI } from '../services/api';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const Clusters = () => {
  const [clusters, setClusters] = useState([]);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [clusterMetrics, setClusterMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deletingCluster, setDeletingCluster] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCluster, setNewCluster] = useState({
    name: '',
    worker_nodes: 2,
    total_cores: 4,
    total_memory: '4g'
  });

  useEffect(() => {
    loadClusters();
  }, []);

  useEffect(() => {
    if (clusters.length > 0 && !selectedCluster) {
      setSelectedCluster(clusters[0]);
    }
  }, [clusters]);

  useEffect(() => {
    if (selectedCluster) {
      loadClusterMetrics(selectedCluster.id);
    }
  }, [selectedCluster]);

  const loadClusters = async () => {
    try {
      const response = await clustersAPI.getAll();
      setClusters(response.data);
    } catch (error) {
      console.error('Failed to load clusters:', error);
    }
  };

  const loadClusterMetrics = async (clusterId) => {
    try {
      const response = await axios.get(`${API_BASE}/clusters/${clusterId}/metrics`);
      setClusterMetrics(response.data);
    } catch (error) {
      console.error('Failed to load cluster metrics:', error);
      setClusterMetrics(null);
    }
  };

  const handleCreateCluster = async () => {
    if (!newCluster.name.trim()) {
      toast.error('Cluster name is required');
      return;
    }

    setLoading(true);
    const loadingToast = toast.loading('Creating cluster...');
    try {
      const response = await clustersAPI.create(newCluster);
      setClusters([...clusters, response.data]);
      setNewCluster({ name: '', worker_nodes: 2, total_cores: 4, total_memory: '4g' });
      setShowCreateModal(false);
      toast.dismiss(loadingToast);
      toast.success(`Cluster "${newCluster.name}" created successfully!`);
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Failed to create cluster:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create cluster';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCluster = async (id) => {
    const cluster = clusters.find(c => c.id === id);
    if (!cluster) return;

    if (!confirm(`Are you sure you want to delete cluster "${cluster.name}"?`)) {
      return;
    }

    setDeletingCluster(id);
    const loadingToast = toast.loading('Deleting cluster...');
    try {
      await clustersAPI.delete(id);
      const updatedClusters = clusters.filter(c => c.id !== id);
      setClusters(updatedClusters);
      if (selectedCluster?.id === id) {
        setSelectedCluster(updatedClusters[0] || null);
      }
      toast.dismiss(loadingToast);
      toast.success(`Cluster "${cluster.name}" deleted successfully!`);
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Failed to delete cluster:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete cluster';
      toast.error(errorMessage);
    } finally {
      setDeletingCluster(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'secondary';
      case 'error':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="space-y-6">
      <Card
        title="Spark Clusters"
        subtitle="Manage and monitor your Apache Spark clusters"
        action={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={loadClusters}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Cluster
            </Button>
          </div>
        }
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cluster List */}
          <div className="lg:col-span-1">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Available Clusters</h3>
            <div className="space-y-2">
              {clusters.length === 0 ? (
                <div className="text-center py-8">
                  <Server className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <p className="text-sm text-gray-600">No clusters available</p>
                  <Button size="sm" className="mt-3" onClick={() => setShowCreateModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Cluster
                  </Button>
                </div>
              ) : (
                clusters.map((cluster) => (
                  <button
                    key={cluster.id}
                    onClick={() => setSelectedCluster(cluster)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                      selectedCluster?.id === cluster.id
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center">
                        <Server className={`w-5 h-5 mr-2 ${
                          cluster.status === 'running' ? 'text-green-500' : 'text-gray-400'
                        }`} />
                        <span className="font-medium text-gray-900">{cluster.name}</span>
                      </div>
                      <Badge variant={getStatusColor(cluster.status)}>
                        {cluster.status}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-500">
                      {cluster.worker_nodes} workers • {cluster.total_cores} cores
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Cluster Details */}
          <div className="lg:col-span-2">
            {selectedCluster ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{selectedCluster.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Cluster ID: <code className="text-xs bg-gray-100 px-2 py-1 rounded">{selectedCluster.id}</code>
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => loadClusterMetrics(selectedCluster.id)}
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Refresh Metrics
                    </Button>
                    {selectedCluster.ui_url && (
                      <Button
                        variant="secondary"
                        onClick={() => window.open(`http://localhost:8080`, '_blank')}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Spark UI
                      </Button>
                    )}
                    {selectedCluster.id !== 'spark-cluster-default' && (
                      <Button
                        variant="danger"
                        onClick={() => handleDeleteCluster(selectedCluster.id)}
                        disabled={deletingCluster === selectedCluster.id}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        {deletingCluster === selectedCluster.id ? 'Deleting...' : 'Delete'}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Status Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <Activity className="w-5 h-5 text-green-600" />
                      <Badge variant={getStatusColor(selectedCluster.status)}>
                        {selectedCluster.status}
                      </Badge>
                    </div>
                    <div className="text-sm font-medium text-green-900">Status</div>
                  </div>

                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between mb-2">
                      <Server className="w-5 h-5 text-blue-600" />
                      <span className="text-2xl font-bold text-blue-900">{selectedCluster.worker_nodes}</span>
                    </div>
                    <div className="text-sm font-medium text-blue-900">Worker Nodes</div>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center justify-between mb-2">
                      <Cpu className="w-5 h-5 text-purple-600" />
                      <span className="text-2xl font-bold text-purple-900">{selectedCluster.total_cores}</span>
                    </div>
                    <div className="text-sm font-medium text-purple-900">Total Cores</div>
                  </div>

                  <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
                    <div className="flex items-center justify-between mb-2">
                      <HardDrive className="w-5 h-5 text-orange-600" />
                      <span className="text-2xl font-bold text-orange-900">{selectedCluster.total_memory}</span>
                    </div>
                    <div className="text-sm font-medium text-orange-900">Total Memory</div>
                  </div>
                </div>

                {/* Cluster Metrics */}
                {clusterMetrics && (
                  <div className="space-y-4">
                    {/* Runtime Info */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        Runtime Information
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-600">Uptime</p>
                          <p className="text-sm font-medium text-gray-900">{clusterMetrics.uptime || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600">Active Applications</p>
                          <p className="text-sm font-medium text-gray-900">{clusterMetrics.applications?.length || 0}</p>
                        </div>
                      </div>
                    </div>

                    {/* Resource Usage */}
                    {clusterMetrics.resources && (
                      <div className="bg-gradient-to-br from-teal-50 to-teal-100 p-4 rounded-lg border border-teal-200">
                        <h4 className="text-sm font-semibold text-teal-900 mb-3 flex items-center">
                          <Zap className="w-4 h-4 mr-2" />
                          Resource Usage
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-xs text-teal-700">Cores</p>
                            <p className="text-sm font-medium text-teal-900">
                              {clusterMetrics.resources.cores_used} / {clusterMetrics.resources.cores_available} used
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-teal-700">Memory</p>
                            <p className="text-sm font-medium text-teal-900">
                              {clusterMetrics.resources.memory_used} / {clusterMetrics.resources.memory_available}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Applications */}
                    {clusterMetrics.applications && clusterMetrics.applications.length > 0 && (
                      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="text-sm font-semibold text-gray-900 mb-3">Active Applications</h4>
                        <div className="space-y-2">
                          {clusterMetrics.applications.map((app, idx) => (
                            <div key={idx} className="bg-white p-3 rounded border border-gray-200">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{app.name}</p>
                                  <p className="text-xs text-gray-600">ID: {app.id}</p>
                                </div>
                                <Badge variant="success">{app.status}</Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Executors */}
                    {clusterMetrics.executors && clusterMetrics.executors.length > 0 && (
                      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="text-sm font-semibold text-gray-900 mb-3">Executors</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {clusterMetrics.executors.map((executor, idx) => (
                            <div key={idx} className="bg-white p-2 rounded border border-gray-200 text-sm">
                              <p className="font-medium text-gray-900">{executor.host}</p>
                              <p className="text-xs text-gray-600">
                                Cores: {executor.cores} • Memory: {executor.memory}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Configuration Details */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h4 className="text-sm font-semibold text-gray-900 mb-4">Configuration</h4>
                  <dl className="grid grid-cols-1 gap-4">
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Master URL</dt>
                      <dd className="mt-1">
                        <code className="text-sm bg-white px-3 py-2 rounded border border-gray-300 block">
                          {selectedCluster.master_url}
                        </code>
                      </dd>
                    </div>
                    {selectedCluster.ui_url && (
                      <div>
                        <dt className="text-sm font-medium text-gray-600">UI URL</dt>
                        <dd className="mt-1">
                          <code className="text-sm bg-white px-3 py-2 rounded border border-gray-300 block">
                            {selectedCluster.ui_url}
                          </code>
                        </dd>
                      </div>
                    )}
                    <div>
                      <dt className="text-sm font-medium text-gray-600">Created</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {new Date(selectedCluster.created_at).toLocaleString()}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            ) : (
              <div className="text-center py-20">
                <Server className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">Select a cluster to view details</p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Create Cluster Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Cluster"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cluster Name
            </label>
            <input
              type="text"
              value={newCluster.name}
              onChange={(e) => setNewCluster({ ...newCluster, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="My Spark Cluster"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Worker Nodes
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={newCluster.worker_nodes}
              onChange={(e) => setNewCluster({ ...newCluster, worker_nodes: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Total Cores
            </label>
            <input
              type="number"
              min="1"
              max="32"
              value={newCluster.total_cores}
              onChange={(e) => setNewCluster({ ...newCluster, total_cores: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Total Memory
            </label>
            <input
              type="text"
              value={newCluster.total_memory}
              onChange={(e) => setNewCluster({ ...newCluster, total_memory: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="4g"
            />
            <p className="mt-1 text-xs text-gray-500">
              Specify memory with unit (e.g., 4g, 8g, 2048m)
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateCluster}
              disabled={loading || !newCluster.name.trim()}
            >
              {loading ? 'Creating...' : 'Create Cluster'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Clusters;

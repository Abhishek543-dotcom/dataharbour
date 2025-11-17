import { useState, useEffect } from 'react';
import { Workflow, Play, Pause, RefreshCw, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const Airflow = () => {
  const [statistics, setStatistics] = useState(null);
  const [dags, setDags] = useState([]);
  const [selectedDag, setSelectedDag] = useState(null);
  const [dagRuns, setDagRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchStatistics();
    fetchDags();
    fetchHealth();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/airflow/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE}/airflow/health`);
      setHealth(response.data);
    } catch (error) {
      console.error('Error fetching health:', error);
      setHealth({ status: 'unhealthy' });
    }
  };

  const fetchDags = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/airflow/dags?limit=100`);
      setDags(response.data.dags || []);
    } catch (error) {
      console.error('Error fetching DAGs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDagRuns = async (dagId) => {
    setLoading(true);
    setSelectedDag(dagId);
    try {
      const response = await axios.get(`${API_BASE}/airflow/dags/${dagId}/runs?limit=25`);
      setDagRuns(response.data.dag_runs || []);
    } catch (error) {
      console.error('Error fetching DAG runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerDag = async (dagId) => {
    try {
      await axios.post(`${API_BASE}/airflow/dags/${dagId}/trigger`, {});
      fetchDags();
      if (selectedDag === dagId) {
        fetchDagRuns(dagId);
      }
    } catch (error) {
      console.error('Error triggering DAG:', error);
    }
  };

  const pauseDag = async (dagId) => {
    try {
      await axios.post(`${API_BASE}/airflow/dags/${dagId}/pause`);
      fetchDags();
    } catch (error) {
      console.error('Error pausing DAG:', error);
    }
  };

  const unpauseDag = async (dagId) => {
    try {
      await axios.post(`${API_BASE}/airflow/dags/${dagId}/unpause`);
      fetchDags();
    } catch (error) {
      console.error('Error unpausing DAG:', error);
    }
  };

  const getStateColor = (state) => {
    switch (state?.toLowerCase()) {
      case 'success':
        return 'success';
      case 'running':
        return 'warning';
      case 'failed':
        return 'error';
      case 'queued':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Airflow Orchestration</h1>
          <p className="text-gray-600 mt-1">Manage DAGs, monitor runs, and view statistics</p>
        </div>
        <div className="flex items-center gap-3">
          {health && (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
              health.status === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              } animate-pulse`} />
              <span className="text-sm font-medium">{health.status}</span>
            </div>
          )}
          <Button variant="secondary" onClick={() => { fetchStatistics(); fetchDags(); fetchHealth(); }}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid grid-cols-4 gap-6">
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary-100 rounded-lg">
                  <Workflow className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total DAGs</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.total_dags}</p>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-green-100 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.success_rate}%</p>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <Loader className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Running Tasks</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.running_tasks}</p>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Play className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active DAGs</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.active_dags}</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* DAGs List */}
        <div className="col-span-5">
          <Card className="h-full">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">DAGs</h3>
            </div>
            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {dags.map((dag) => (
                <div
                  key={dag.dag_id}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedDag === dag.dag_id ? 'bg-primary-50' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => fetchDagRuns(dag.dag_id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 truncate">{dag.dag_id}</h4>
                        {dag.is_paused && (
                          <Badge variant="warning">Paused</Badge>
                        )}
                      </div>
                      {dag.description && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {dag.description}
                        </p>
                      )}
                      {dag.schedule_interval && (
                        <div className="flex items-center gap-1 text-xs text-gray-500 mt-2">
                          <Clock className="w-3 h-3" />
                          {dag.schedule_interval}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-1 ml-3">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          triggerDag(dag.dag_id);
                        }}
                      >
                        <Play className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          dag.is_paused ? unpauseDag(dag.dag_id) : pauseDag(dag.dag_id);
                        }}
                      >
                        <Pause className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* DAG Runs */}
        <div className="col-span-7">
          {selectedDag ? (
            <Card>
              <div className="p-4 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">
                  DAG Runs: {selectedDag}
                </h3>
              </div>
              <div className="p-4">
                {dagRuns.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Workflow className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No runs found for this DAG</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {dagRuns.map((run) => (
                      <div
                        key={run.dag_run_id}
                        className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Badge variant={getStateColor(run.state)}>
                                {run.state}
                              </Badge>
                              <span className="text-sm text-gray-600">
                                {run.dag_run_id}
                              </span>
                            </div>
                            <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                              <div>
                                <span className="text-gray-500">Execution:</span>
                                <span className="ml-2 text-gray-900">
                                  {new Date(run.execution_date).toLocaleString()}
                                </span>
                              </div>
                              {run.start_date && (
                                <div>
                                  <span className="text-gray-500">Started:</span>
                                  <span className="ml-2 text-gray-900">
                                    {new Date(run.start_date).toLocaleString()}
                                  </span>
                                </div>
                              )}
                              {run.end_date && (
                                <div>
                                  <span className="text-gray-500">Ended:</span>
                                  <span className="ml-2 text-gray-900">
                                    {new Date(run.end_date).toLocaleString()}
                                  </span>
                                </div>
                              )}
                              {run.external_trigger && (
                                <div>
                                  <Badge variant="info">External Trigger</Badge>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <Card>
              <div className="p-12 text-center text-gray-500">
                <Workflow className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Select a DAG to view its runs</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Airflow;

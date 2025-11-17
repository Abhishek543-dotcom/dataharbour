import { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Network, Server, RefreshCw, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const Monitoring = () => {
  const [metrics, setMetrics] = useState(null);
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [serviceLogs, setServiceLogs] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMetrics();
    fetchServices();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchMetrics();
      fetchServices();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/monitoring/metrics`);
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API_BASE}/monitoring/services`);
      setServices(response.data.services || []);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const fetchServiceLogs = async (serviceName) => {
    setLoading(true);
    setSelectedService(serviceName);
    try {
      const response = await axios.get(
        `${API_BASE}/monitoring/services/${serviceName}/logs?lines=100`
      );
      setServiceLogs(response.data.logs || 'No logs available');
    } catch (error) {
      console.error('Error fetching service logs:', error);
      setServiceLogs('Error loading logs');
    } finally {
      setLoading(false);
    }
  };

  const getServiceStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'stopped':
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getServiceStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'healthy':
        return 'success';
      case 'stopped':
      case 'unhealthy':
        return 'error';
      default:
        return 'warning';
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
          <p className="text-gray-600 mt-1">Real-time system metrics and service health</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => {
            fetchMetrics();
            fetchServices();
          }}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* System Metrics */}
      {metrics && (
        <div className="grid grid-cols-4 gap-6">
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Cpu className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">CPU Usage</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.cpu_percent}%</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${metrics.cpu_percent}%` }}
                />
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <HardDrive className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Memory Usage</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.memory_percent}%</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${metrics.memory_percent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {formatBytes(metrics.memory_used)} / {formatBytes(metrics.memory_total)}
              </p>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <HardDrive className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Disk Usage</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.disk_percent}%</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all"
                  style={{ width: `${metrics.disk_percent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {formatBytes(metrics.disk_used)} / {formatBytes(metrics.disk_total)}
              </p>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <Network className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Network</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatBytes(metrics.network_sent)}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                <div>
                  <span className="text-gray-500">Sent:</span>
                  <span className="ml-1">{formatBytes(metrics.network_sent)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Recv:</span>
                  <span className="ml-1">{formatBytes(metrics.network_recv)}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Services */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-5">
          <Card>
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Services Status</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {services.map((service) => (
                <div
                  key={service.name}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedService === service.name ? 'bg-primary-50' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => fetchServiceLogs(service.name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getServiceStatusIcon(service.status)}
                      <div>
                        <h4 className="font-medium text-gray-900">{service.name}</h4>
                        <p className="text-sm text-gray-500">{service.description}</p>
                      </div>
                    </div>
                    <Badge variant={getServiceStatusBadge(service.status)}>
                      {service.status}
                    </Badge>
                  </div>
                  {service.url && (
                    <div className="mt-2 text-xs text-gray-500">
                      <a
                        href={service.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {service.url}
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="col-span-7">
          {selectedService ? (
            <Card>
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">
                    Logs: {selectedService}
                  </h3>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => fetchServiceLogs(selectedService)}
                    disabled={loading}
                  >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </div>
              <div className="p-4">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto max-h-[500px] overflow-y-auto font-mono">
                  {serviceLogs}
                </pre>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="p-12 text-center text-gray-500">
                <Server className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Select a service to view its logs</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Monitoring;

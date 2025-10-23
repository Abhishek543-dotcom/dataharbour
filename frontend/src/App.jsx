import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import Notebooks from './pages/Notebooks';
import Clusters from './pages/Clusters';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';
import websocketService from './services/websocket';
import useStore from './store/useStore';

function App() {
  const { setWsConnected, updateJobInList, updateMetrics } = useStore();

  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect();

    // Subscribe to connection status
    const unsubConnection = websocketService.on('connection', (data) => {
      setWsConnected(data.status === 'connected');
    });

    // Subscribe to job updates
    const unsubJobUpdate = websocketService.on('job_update', (data) => {
      updateJobInList(data);
    });

    // Subscribe to metrics updates
    const unsubMetrics = websocketService.on('metrics_update', (data) => {
      updateMetrics(data);
    });

    // Cleanup on unmount
    return () => {
      unsubConnection();
      unsubJobUpdate();
      unsubMetrics();
      websocketService.disconnect();
    };
  }, [setWsConnected, updateJobInList, updateMetrics]);

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/notebooks" element={<Notebooks />} />
        <Route path="/clusters" element={<Clusters />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;

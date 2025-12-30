import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import Notebooks from './pages/Notebooks';
import Database from './pages/Database';
import Airflow from './pages/Airflow';
import Storage from './pages/Storage';
import Clusters from './pages/Clusters';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
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
    <AuthProvider>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <Routes>
        {/* Auth routes (no layout) */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* App routes (with layout) */}
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/notebooks" element={<Notebooks />} />
          <Route path="/database" element={<Database />} />
          <Route path="/airflow" element={<Airflow />} />
          <Route path="/storage" element={<Storage />} />
          <Route path="/clusters" element={<Clusters />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;

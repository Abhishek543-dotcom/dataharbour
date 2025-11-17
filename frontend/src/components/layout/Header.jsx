import { useLocation } from 'react-router-dom';
import { Wifi, WifiOff } from 'lucide-react';
import useStore from '../../store/useStore';

const pageTitles = {
  '/': 'Dashboard',
  '/jobs': 'Jobs',
  '/notebooks': 'Notebooks',
  '/database': 'Database Explorer',
  '/airflow': 'Airflow Orchestration',
  '/storage': 'Storage Browser',
  '/clusters': 'Clusters',
  '/monitoring': 'Monitoring',
  '/settings': 'Settings',
};

const Header = () => {
  const location = useLocation();
  const wsConnected = useStore((state) => state.wsConnected);
  const pageTitle = pageTitles[location.pathname] || 'DataHarbour';

  return (
    <header className="bg-white bg-opacity-95 backdrop-blur-lg border-b border-gray-200 shadow-sm">
      <div className="px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            {pageTitle}
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {/* WebSocket Status */}
          <div className="flex items-center gap-2 text-sm">
            {wsConnected ? (
              <>
                <Wifi className="w-4 h-4 text-green-500" />
                <span className="text-gray-600">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span className="text-gray-600">Disconnected</span>
              </>
            )}
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-white font-medium">
              A
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

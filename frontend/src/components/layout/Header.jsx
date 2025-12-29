import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Wifi, WifiOff, LogOut, User } from 'lucide-react';
import { useState } from 'react';
import useStore from '../../store/useStore';
import { useAuth } from '../../context/AuthContext';

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
  const navigate = useNavigate();
  const wsConnected = useStore((state) => state.wsConnected);
  const { user, isAuthenticated, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const pageTitle = pageTitles[location.pathname] || 'DataHarbour';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getUserInitial = () => {
    if (user?.username) {
      return user.username.charAt(0).toUpperCase();
    }
    return 'U';
  };

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
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-700">{user?.username || 'User'}</div>
                  {user?.email && (
                    <div className="text-xs text-gray-500">{user.email}</div>
                  )}
                </div>
                <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-white font-medium">
                  {getUserInitial()}
                </div>
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <Link
                    to="/settings"
                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <User className="w-4 h-4" />
                    Profile Settings
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              to="/login"
              className="px-4 py-2 bg-gradient-primary text-white rounded-lg hover:opacity-90 transition-opacity text-sm font-medium"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;

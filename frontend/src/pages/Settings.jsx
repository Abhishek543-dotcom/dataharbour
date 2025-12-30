import { useState } from 'react';
import { User, Palette, Key, Info, Save, Copy, Check } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';

const Settings = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [copied, setCopied] = useState(false);

  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || ''
  });

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'system', label: 'System', icon: Info }
  ];

  const handleSaveProfile = () => {
    console.log('Save profile:', profileData);
    // TODO: Implement API call to update profile
  };

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    // TODO: Apply theme to document
  };

  const handleGenerateAPIKey = () => {
    console.log('Generate API key');
    // TODO: Implement API key generation
  };

  const handleCopyKey = (key) => {
    navigator.clipboard.writeText(key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <Card
        title="Settings"
        subtitle="Manage your account and application preferences"
      >
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Tabs Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all ${
                      activeTab === tab.id
                        ? 'bg-purple-100 text-purple-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="lg:col-span-3">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    Update your personal information and account details
                  </p>
                </div>

                {user ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={profileData.full_name}
                        onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        placeholder="John Doe"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        placeholder="john@example.com"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        value={profileData.username}
                        disabled
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                      />
                      <p className="mt-1 text-xs text-gray-500">Username cannot be changed</p>
                    </div>

                    <div className="pt-4">
                      <Button onClick={handleSaveProfile}>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-sm text-yellow-800">
                      You are not logged in. <a href="/login" className="font-medium underline">Sign in</a> to manage your profile.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Appearance Tab */}
            {activeTab === 'appearance' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Appearance</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    Customize the look and feel of the application
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Theme
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {['light', 'dark', 'system'].map((themeOption) => (
                      <button
                        key={themeOption}
                        onClick={() => handleThemeChange(themeOption)}
                        className={`p-4 border-2 rounded-lg text-left transition-all ${
                          theme === themeOption
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900 capitalize">{themeOption}</span>
                          {theme === themeOption && (
                            <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                              <Check className="w-3 h-3 text-white" />
                            </div>
                          )}
                        </div>
                        <p className="text-xs text-gray-600">
                          {themeOption === 'light' && 'Classic light theme'}
                          {themeOption === 'dark' && 'Dark mode for low light'}
                          {themeOption === 'system' && 'Match system settings'}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> Dark mode implementation coming soon! Currently only light theme is available.
                  </p>
                </div>
              </div>
            )}

            {/* API Keys Tab */}
            {activeTab === 'api-keys' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">API Keys</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    Manage API keys for programmatic access to DataHarbour
                  </p>
                </div>

                {user ? (
                  <>
                    <div>
                      <Button onClick={handleGenerateAPIKey}>
                        <Key className="w-4 h-4 mr-2" />
                        Generate New API Key
                      </Button>
                    </div>

                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-700">Active Keys</h4>
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <p className="text-sm text-gray-600 text-center py-4">
                          No API keys generated yet
                        </p>
                      </div>
                    </div>

                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="text-sm text-yellow-800">
                        <strong>Security tip:</strong> Keep your API keys secure and never share them publicly. You can revoke keys at any time.
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-sm text-yellow-800">
                      You must be logged in to manage API keys. <a href="/login" className="font-medium underline">Sign in</a> to continue.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* System Tab */}
            {activeTab === 'system' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    View application and service status
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Application</h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Version</dt>
                        <dd className="text-sm font-medium text-gray-900">1.0.0</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Environment</dt>
                        <dd className="text-sm font-medium text-gray-900">Development</dd>
                      </div>
                    </dl>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Backend Services</h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between items-center">
                        <dt className="text-sm text-gray-600">API Server</dt>
                        <dd className="flex items-center">
                          <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                          <span className="text-sm font-medium text-gray-900">Running</span>
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">API URL</dt>
                        <dd className="text-sm font-medium text-gray-900">http://localhost:8000</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">WebSocket</dt>
                        <dd className="text-sm font-medium text-gray-900">ws://localhost:8000/ws</dd>
                      </div>
                    </dl>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Data Services</h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">PostgreSQL</dt>
                        <dd className="text-sm font-medium text-gray-900">postgres:5432</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">MinIO</dt>
                        <dd className="text-sm font-medium text-gray-900">minio:9000</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Spark Master</dt>
                        <dd className="text-sm font-medium text-gray-900">spark://spark:7077</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-600">Airflow</dt>
                        <dd className="text-sm font-medium text-gray-900">http://localhost:8081</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Settings;

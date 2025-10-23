import { Settings as SettingsIcon } from 'lucide-react';
import Card from '../components/ui/Card';

const Settings = () => {
  return (
    <div className="space-y-6">
      <Card title="Settings" subtitle="Application settings and preferences">
        <div className="text-center py-12">
          <SettingsIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">Settings page - Coming soon</p>
        </div>
      </Card>
    </div>
  );
};

export default Settings;

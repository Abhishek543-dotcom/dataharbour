import { Activity } from 'lucide-react';
import Card from '../components/ui/Card';

const Monitoring = () => {
  return (
    <div className="space-y-6">
      <Card title="Monitoring" subtitle="System metrics and service health">
        <div className="text-center py-12">
          <Activity className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">Monitoring page - Coming soon</p>
        </div>
      </Card>
    </div>
  );
};

export default Monitoring;

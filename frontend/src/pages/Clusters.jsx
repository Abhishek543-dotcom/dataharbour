import { Server } from 'lucide-react';
import Card from '../components/ui/Card';

const Clusters = () => {
  return (
    <div className="space-y-6">
      <Card title="Clusters" subtitle="Manage your Spark clusters">
        <div className="text-center py-12">
          <Server className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">Clusters page - Coming soon</p>
        </div>
      </Card>
    </div>
  );
};

export default Clusters;

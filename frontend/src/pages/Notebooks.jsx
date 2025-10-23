import { FileText } from 'lucide-react';
import Card from '../components/ui/Card';

const Notebooks = () => {
  return (
    <div className="space-y-6">
      <Card title="Notebooks" subtitle="Manage your Jupyter-style notebooks">
        <div className="text-center py-12">
          <FileText className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">Notebooks page - Coming soon with CodeMirror editor</p>
        </div>
      </Card>
    </div>
  );
};

export default Notebooks;

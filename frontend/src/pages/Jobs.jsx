import { useEffect, useState } from 'react';
import { Briefcase, Plus, RefreshCw, Eye, Square, RotateCcw } from 'lucide-react';
import useStore from '../store/useStore';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';

const Jobs = () => {
  const { jobs, loadingJobs, fetchJobs, createJob, killJob, restartJob } = useStore();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newJob, setNewJob] = useState({ name: '', code: '' });

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleCreateJob = async () => {
    try {
      await createJob(newJob);
      setIsCreateModalOpen(false);
      setNewJob({ name: '', code: '' });
    } catch (error) {
      console.error('Failed to create job:', error);
    }
  };

  return (
    <div className="space-y-6">
      <Card
        title="Jobs"
        subtitle={`${jobs.length} total jobs`}
        actions={
          <>
            <Button
              variant="ghost"
              size="sm"
              icon={<RefreshCw className="w-4 h-4" />}
              onClick={() => fetchJobs()}
            >
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<Plus className="w-4 h-4" />}
              onClick={() => setIsCreateModalOpen(true)}
            >
              New Job
            </Button>
          </>
        }
      >
        {loadingJobs ? (
          <div className="text-center py-8">Loading...</div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12">
            <Briefcase className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No jobs found. Create your first job!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cluster
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {job.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {job.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={job.status}>{job.status}</Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {job.cluster}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {job.duration || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <Button variant="ghost" size="sm" icon={<Eye className="w-4 h-4" />} />
                      {job.status === 'running' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Square className="w-4 h-4" />}
                          onClick={() => killJob(job.id)}
                        />
                      )}
                      {(job.status === 'completed' || job.status === 'failed') && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<RotateCcw className="w-4 h-4" />}
                          onClick={() => restartJob(job.id)}
                        />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create Job Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Job"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreateJob}>
              Create Job
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Job Name</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={newJob.name}
              onChange={(e) => setNewJob({ ...newJob, name: e.target.value })}
              placeholder="My PySpark Job"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">PySpark Code</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              rows={10}
              value={newJob.code}
              onChange={(e) => setNewJob({ ...newJob, code: e.target.value })}
              placeholder="from pyspark.sql import SparkSession&#10;spark = SparkSession.builder.getOrCreate()&#10;..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Jobs;

import { useEffect, useState } from 'react';
import { Briefcase, Plus, RefreshCw, Eye, Square, RotateCcw, Calendar, Workflow } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store/useStore';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const Jobs = () => {
  const { jobs, loadingJobs, fetchJobs, createJob, killJob, restartJob } = useStore();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [selectedJobForSchedule, setSelectedJobForSchedule] = useState(null);
  const [scheduleInterval, setScheduleInterval] = useState('0 0 * * *'); // Daily at midnight
  const [newJob, setNewJob] = useState({ name: '', code: '' });
  const [isCreatingJob, setIsCreatingJob] = useState(false);
  const [formErrors, setFormErrors] = useState({ name: '', code: '' });

  useEffect(() => {
    fetchJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount

  const validateForm = () => {
    const errors = { name: '', code: '' };
    let isValid = true;

    if (!newJob.name.trim()) {
      errors.name = 'Job name is required';
      isValid = false;
    } else if (newJob.name.trim().length < 3) {
      errors.name = 'Job name must be at least 3 characters';
      isValid = false;
    }

    if (!newJob.code.trim()) {
      errors.code = 'PySpark code is required';
      isValid = false;
    } else if (newJob.code.trim().length < 10) {
      errors.code = 'Code must be at least 10 characters';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleCreateJob = async () => {
    // Clear previous errors
    setFormErrors({ name: '', code: '' });

    // Validate form
    if (!validateForm()) {
      toast.error('Please fix the form errors');
      return;
    }

    setIsCreatingJob(true);
    try {
      const loadingToast = toast.loading('Creating Spark job...');
      await createJob(newJob);
      toast.dismiss(loadingToast);
      toast.success(`Job "${newJob.name}" created successfully!`);
      setIsCreateModalOpen(false);
      setNewJob({ name: '', code: '' });
      setFormErrors({ name: '', code: '' });
    } catch (error) {
      console.error('Failed to create job:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create job';
      toast.error(errorMessage);
    } finally {
      setIsCreatingJob(false);
    }
  };

  const handleScheduleJob = (job) => {
    setSelectedJobForSchedule(job);
    setIsScheduleModalOpen(true);
  };

  const handleConvertToDAG = async () => {
    if (!selectedJobForSchedule) return;

    const loadingToast = toast.loading('Creating Airflow DAG...');
    try {
      const response = await axios.post(
        `${API_BASE}/jobs/${selectedJobForSchedule.id}/convert-to-dag?schedule_interval=${encodeURIComponent(scheduleInterval)}`
      );
      toast.dismiss(loadingToast);
      toast.success(response.data.message || 'DAG created successfully! Check Airflow page.');
      setIsScheduleModalOpen(false);
      setSelectedJobForSchedule(null);
      setScheduleInterval('0 0 * * *');
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error('Failed to schedule job:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to schedule job';
      toast.error(errorMessage);
    }
  };

  const schedulePresets = [
    { label: 'Every Hour', value: '0 * * * *' },
    { label: 'Daily at Midnight', value: '0 0 * * *' },
    { label: 'Daily at 6 AM', value: '0 6 * * *' },
    { label: 'Weekly (Monday)', value: '0 0 * * 1' },
    { label: 'Monthly (1st)', value: '0 0 1 * *' },
  ];

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Workflow className="w-5 h-5 text-purple-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-purple-900">Jobs ↔ Airflow Integration</h3>
            <p className="text-sm text-purple-700 mt-1">
              Jobs allow quick Spark code execution. Click "Schedule as DAG" to convert any job into an Airflow workflow for recurring execution!
            </p>
          </div>
        </div>
      </div>

      <Card
        title="Spark Jobs"
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
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Calendar className="w-4 h-4" />}
                        onClick={() => handleScheduleJob(job)}
                        title="Schedule as Airflow DAG"
                      />
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
        title="Create New Spark Job"
        size="lg"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => {
                setIsCreateModalOpen(false);
                setNewJob({ name: '', code: '' });
                setFormErrors({ name: '', code: '' });
              }}
              disabled={isCreatingJob}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateJob}
              disabled={isCreatingJob}
            >
              {isCreatingJob ? 'Creating...' : 'Create Job'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Job Name</label>
            <input
              type="text"
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:border-transparent ${
                formErrors.name
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-primary-500'
              }`}
              value={newJob.name}
              onChange={(e) => {
                setNewJob({ ...newJob, name: e.target.value });
                if (formErrors.name) setFormErrors({ ...formErrors, name: '' });
              }}
              placeholder="My PySpark Job"
              disabled={isCreatingJob}
            />
            {formErrors.name && (
              <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">PySpark Code</label>
            <textarea
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:border-transparent font-mono text-sm ${
                formErrors.code
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-primary-500'
              }`}
              rows={10}
              value={newJob.code}
              onChange={(e) => {
                setNewJob({ ...newJob, code: e.target.value });
                if (formErrors.code) setFormErrors({ ...formErrors, code: '' });
              }}
              placeholder="from pyspark.sql import SparkSession&#10;spark = SparkSession.builder.getOrCreate()&#10;..."
              disabled={isCreatingJob}
            />
            {formErrors.code && (
              <p className="mt-1 text-sm text-red-600">{formErrors.code}</p>
            )}
          </div>
        </div>
      </Modal>

      {/* Schedule as DAG Modal */}
      <Modal
        isOpen={isScheduleModalOpen}
        onClose={() => {
          setIsScheduleModalOpen(false);
          setSelectedJobForSchedule(null);
        }}
        title={`Schedule "${selectedJobForSchedule?.name}" as Airflow DAG`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsScheduleModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleConvertToDAG}>
              <Workflow className="w-4 h-4 mr-2" />
              Create DAG
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              This will create an Airflow DAG that runs this Spark job on a schedule. The DAG will appear in the Airflow page shortly.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Schedule Interval (Cron)</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              value={scheduleInterval}
              onChange={(e) => setScheduleInterval(e.target.value)}
              placeholder="0 0 * * *"
            />
            <p className="text-xs text-gray-500 mt-1">Cron expression for scheduling (e.g., "0 0 * * *" = daily at midnight)</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Quick Presets</label>
            <div className="grid grid-cols-2 gap-2">
              {schedulePresets.map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => setScheduleInterval(preset.value)}
                  className={`px-3 py-2 border rounded-lg text-sm transition-colors ${
                    scheduleInterval === preset.value
                      ? 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-gray-300 hover:border-gray-400 text-gray-700'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {selectedJobForSchedule && (
            <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Job Details</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <p><strong>ID:</strong> {selectedJobForSchedule.id}</p>
                <p><strong>Name:</strong> {selectedJobForSchedule.name}</p>
                <p><strong>Cluster:</strong> {selectedJobForSchedule.cluster}</p>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Jobs;

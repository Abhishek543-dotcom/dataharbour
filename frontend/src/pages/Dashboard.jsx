import { useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { FileText, Briefcase, Server, TrendingUp } from 'lucide-react';
import useStore from '../store/useStore';
import Card from '../components/ui/Card';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const StatCard = ({ title, value, icon: Icon, trend }) => (
  <Card className="hover:shadow-xl transition-shadow">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600 mb-1">{title}</p>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        {trend && (
          <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            {trend}
          </p>
        )}
      </div>
      <div className="p-3 bg-gradient-primary rounded-lg">
        <Icon className="w-8 h-8 text-white" />
      </div>
    </div>
  </Card>
);

const Dashboard = () => {
  const { dashboardStats, dashboardTrends, loadingDashboard, fetchDashboardData } = useStore();

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount

  const chartData = {
    labels: dashboardTrends?.labels || [],
    datasets: [
      {
        label: 'Completed Jobs',
        data: dashboardTrends?.completed || [],
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Failed Jobs',
        data: dashboardTrends?.failed || [],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  if (loadingDashboard) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Notebooks"
          value={dashboardStats?.total_notebooks || 0}
          icon={FileText}
        />
        <StatCard
          title="Total Jobs"
          value={dashboardStats?.total_jobs || 0}
          icon={Briefcase}
          trend="+12% from last week"
        />
        <StatCard
          title="Active Clusters"
          value={dashboardStats?.active_clusters || 0}
          icon={Server}
        />
        <StatCard
          title="Running Jobs"
          value={dashboardStats?.running_jobs || 0}
          icon={TrendingUp}
        />
      </div>

      {/* Job Trends Chart */}
      <Card title="Job Completion Trends" subtitle="Last 7 days">
        <div className="h-80">
          <Line data={chartData} options={chartOptions} />
        </div>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Completed Jobs">
          <p className="text-4xl font-bold text-green-600">
            {dashboardStats?.completed_jobs || 0}
          </p>
          <p className="text-sm text-gray-600 mt-2">Successfully completed</p>
        </Card>
        <Card title="Failed Jobs">
          <p className="text-4xl font-bold text-red-600">
            {dashboardStats?.failed_jobs || 0}
          </p>
          <p className="text-sm text-gray-600 mt-2">Need attention</p>
        </Card>
        <Card title="Success Rate">
          <p className="text-4xl font-bold text-blue-600">
            {dashboardStats?.total_jobs > 0
              ? Math.round(
                  (dashboardStats.completed_jobs / dashboardStats.total_jobs) * 100
                )
              : 0}
            %
          </p>
          <p className="text-sm text-gray-600 mt-2">Overall success rate</p>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;

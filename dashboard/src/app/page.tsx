import { Header } from "@/components/layout/header";
import { ServiceControlPanel } from "@/components/dashboard/service-control-panel";
import { LogsViewer } from "@/components/dashboard/logs-viewer";
import { MetricsPanel } from "@/components/dashboard/metrics-panel";
import { AirflowDagMonitor } from "@/components/dashboard/airflow-dag-monitor";
import { SparkJobTracker } from "@/components/dashboard/spark-job-tracker";
import { MinioFileBrowser } from "@/components/dashboard/minio-file-browser";
import { BackupStatus } from "@/components/dashboard/backup-status";
import { AlertCenter } from "@/components/dashboard/alert-center";

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <ServiceControlPanel />
          </div>
          <div className="md:col-span-2">
            <LogsViewer />
          </div>
          
          <MetricsPanel />
          <AirflowDagMonitor />
          
          <SparkJobTracker />
          <MinioFileBrowser />
          
          <BackupStatus />
          <AlertCenter />
        </div>
      </main>
      <footer className="py-4 text-center text-xs text-muted-foreground border-t">
        DataHarbour &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}

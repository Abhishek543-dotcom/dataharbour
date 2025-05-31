"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ExternalLink, BellRing, Info, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Alert {
  id: string;
  severity: "critical" | "warning" | "info";
  message: string;
  service: string;
  timestamp: string;
  link?: string;
}

const sampleAlerts: Alert[] = [
  { id: "alert1", severity: "critical", message: "PostgreSQL high CPU utilization (>90%)", service: "PostgreSQL", timestamp: "2023-10-27 10:50:00", link: "/metrics/postgres" },
  { id: "alert2", severity: "warning", message: "Airflow DAG 'user_segmentation_pipeline' failed", service: "Airflow", timestamp: "2023-10-27 09:48:00", link: "/airflow/dags/user_segmentation_pipeline" },
  { id: "alert3", severity: "info", message: "Spark worker node disk space >80% full", service: "Spark Worker 1", timestamp: "2023-10-27 08:30:00", link: "/metrics/spark-worker-1" },
  { id: "alert4", severity: "warning", message: "MinIO bucket 'archive' nearing quota", service: "MinIO", timestamp: "2023-10-26 15:00:00" },
];

const SeverityIcon = ({ severity }: { severity: Alert["severity"] }) => {
  switch (severity) {
    case "critical": return <AlertTriangle className="h-4 w-4 text-red-400" />;
    case "warning": return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
    case "info": return <Info className="h-4 w-4 text-blue-400" />;
    default: return <BellRing className="h-4 w-4 text-gray-400" />;
  }
};

export function AlertCenter() {
  const [alerts, setAlerts] = React.useState(sampleAlerts);

  const getSeverityBadgeVariant = (severity: Alert["severity"]): "destructive" | "secondary" | "default" => {
    if (severity === "critical") return "destructive";
    if (severity === "warning") return "secondary";
    return "default";
  };
  
  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prevAlerts => prevAlerts.filter(alert => alert.id !== alertId));
  };


  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <BellRing className="mr-2 h-6 w-6 text-primary" />
          Alert Center
        </CardTitle>
        <CardDescription>Active alerts from Prometheus and other monitoring systems.</CardDescription>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-center text-muted-foreground">
            <CheckCircle className="h-12 w-12 mb-2 text-green-500" />
            <p className="text-lg">No Active Alerts</p>
            <p className="text-sm">All systems are nominal.</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
            {alerts.map((alert) => (
              <div key={alert.id} className="p-3 border rounded-lg bg-card-foreground/5 hover:bg-card-foreground/10 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-start">
                    <SeverityIcon severity={alert.severity} />
                    <div className="ml-2">
                      <p className="text-sm font-medium text-foreground">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {alert.service} - {alert.timestamp}
                      </p>
                    </div>
                  </div>
                  <Badge variant={getSeverityBadgeVariant(alert.severity)} className="capitalize text-xs">
                    {alert.severity}
                  </Badge>
                </div>
                <div className="mt-2 flex justify-end space-x-2">
                  {alert.link && (
                    <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                      View Details <ExternalLink size={12} className="ml-1" />
                    </Button>
                  )}
                   <Button variant="outline" size="sm" className="h-auto py-0.5 px-1.5 text-xs" onClick={() => acknowledgeAlert(alert.id)}>
                     Acknowledge
                   </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

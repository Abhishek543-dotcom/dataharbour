"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PlayCircle, PauseCircle, ListChecks, AlertTriangle, CheckCircle2, XCircle, RefreshCw } from "lucide-react";

interface Dag {
  id: string;
  name: string;
  status: "success" | "running" | "failed" | "queued";
  lastRun: string;
  duration: string;
  isPaused: boolean;
}

const sampleDags: Dag[] = [
  { id: "dag1", name: "daily_sales_etl", status: "success", lastRun: "2023-10-27 08:00:00", duration: "15m 30s", isPaused: false },
  { id: "dag2", name: "user_segmentation_pipeline", status: "running", lastRun: "2023-10-27 10:30:00", duration: "5m 10s (avg)", isPaused: false },
  { id: "dag3", name: "hourly_data_ingestion", status: "failed", lastRun: "2023-10-27 09:45:00", duration: "2m 5s", isPaused: false },
  { id: "dag4", name: "ml_model_retraining", status: "queued", lastRun: "N/A", duration: "N/A", isPaused: true },
  { id: "dag5", name: "weekly_report_generation", status: "success", lastRun: "2023-10-25 02:00:00", duration: "45m 00s", isPaused: false },
];

const StatusIcon = ({ status }: { status: Dag["status"] }) => {
  switch (status) {
    case "success": return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case "running": return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
    case "failed": return <XCircle className="h-4 w-4 text-red-500" />;
    case "queued": return <ListChecks className="h-4 w-4 text-yellow-500" />;
    default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
  }
};


export function AirflowDagMonitor() {
  const [dags, setDags] = React.useState<Dag[]>(sampleDags);

  const togglePauseDag = (dagId: string) => {
    setDags(dags.map(dag => dag.id === dagId ? { ...dag, isPaused: !dag.isPaused } : dag));
  };
  
  const triggerDag = (dagId: string) => {
    // In a real app, this would make an API call
    console.log(`Triggering DAG: ${dagId}`);
     setDags(dags.map(dag => dag.id === dagId ? { ...dag, status: "queued" as Dag["status"] } : dag));
  };

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <ListChecks className="mr-2 h-6 w-6 text-primary" />
          Airflow DAG Monitor
        </CardTitle>
        <CardDescription>View status and manage your Airflow DAGs.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>DAG Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Run</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {dags.map((dag) => (
              <TableRow key={dag.id}>
                <TableCell className="font-medium">{dag.name}</TableCell>
                <TableCell>
                  <Badge variant={dag.status === 'success' ? 'default' : dag.status === 'failed' ? 'destructive' : 'secondary'} 
                         className="capitalize flex items-center gap-1 w-fit">
                    <StatusIcon status={dag.status}/>
                    {dag.status}
                  </Badge>
                </TableCell>
                <TableCell>{dag.lastRun}</TableCell>
                <TableCell>{dag.duration}</TableCell>
                <TableCell className="text-right space-x-1">
                  <Button variant="outline" size="sm" onClick={() => triggerDag(dag.id)} disabled={dag.isPaused || dag.status === 'running'}>
                    <PlayCircle size={16} className="mr-1" /> Trigger
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => togglePauseDag(dag.id)}>
                    {dag.isPaused ? <PlayCircle size={16} className="mr-1" /> : <PauseCircle size={16} className="mr-1" />}
                    {dag.isPaused ? "Unpause" : "Pause"}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Cpu, CheckCircle2, XCircle, RefreshCw, Clock } from "lucide-react";

interface SparkJob {
  id: string;
  name: string;
  status: "SUCCEEDED" | "RUNNING" | "FAILED" | "PENDING";
  submitTime: string;
  duration: string;
  outputPath?: string;
}

const sampleSparkJobs: SparkJob[] = [
  { id: "job_123", name: "Data Ingestion Pipeline", status: "SUCCEEDED", submitTime: "2023-10-27 09:00:00", duration: "25m 10s", outputPath: "s3a://data/output/ingestion/2023-10-27" },
  { id: "job_124", name: "Feature Engineering Task", status: "RUNNING", submitTime: "2023-10-27 10:15:00", duration: "5m 02s", outputPath: "s3a://data/output/features/temp_run_124" },
  { id: "job_125", name: "Model Training (Batch)", status: "FAILED", submitTime: "2023-10-26 14:30:00", duration: "1h 10m 05s", outputPath: "N/A" },
  { id: "job_126", name: "Ad-hoc Query Analysis", status: "PENDING", submitTime: "2023-10-27 10:45:00", duration: "N/A" },
  { id: "job_127", name: "Reporting Aggregation", status: "SUCCEEDED", submitTime: "2023-10-27 01:00:00", duration: "55m 00s", outputPath: "s3a://data/output/reports/daily/2023-10-27" },
];

const StatusInfo = ({ status }: { status: SparkJob["status"] }) => {
  switch (status) {
    case "SUCCEEDED": return { icon: <CheckCircle2 className="h-4 w-4 text-green-500" />, color: "bg-green-500/20 text-green-400" };
    case "RUNNING": return { icon: <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />, color: "bg-blue-500/20 text-blue-400" };
    case "FAILED": return { icon: <XCircle className="h-4 w-4 text-red-500" />, color: "bg-red-500/20 text-red-400" };
    case "PENDING": return { icon: <Clock className="h-4 w-4 text-yellow-500" />, color: "bg-yellow-500/20 text-yellow-400" };
    default: return { icon: <Cpu className="h-4 w-4 text-gray-500" />, color: "bg-gray-500/20 text-gray-400" };
  }
};


export function SparkJobTracker() {
  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <Cpu className="mr-2 h-6 w-6 text-primary" />
          Spark Job Tracker
        </CardTitle>
        <CardDescription>Monitor recent Spark jobs submitted to the cluster.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Job ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Submit Time</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Output Path</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sampleSparkJobs.map((job) => {
              const {icon, color} = StatusInfo({status: job.status});
              return (
              <TableRow key={job.id}>
                <TableCell className="font-mono text-xs">{job.id}</TableCell>
                <TableCell className="font-medium">{job.name}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={`capitalize flex items-center gap-1.5 ${color} border-none`}>
                    {icon}
                    {job.status.toLowerCase()}
                  </Badge>
                </TableCell>
                <TableCell>{job.submitTime}</TableCell>
                <TableCell>{job.duration}</TableCell>
                <TableCell className="text-xs text-muted-foreground truncate max-w-[200px]" title={job.outputPath}>{job.outputPath || "N/A"}</TableCell>
              </TableRow>
            )})}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

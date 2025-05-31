"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

const sampleLogs = {
  jupyter: `[I 2023-10-27 10:00:00.000 ServerApp] Jupyter Server is RRRRRRRRRRRRRRunning!
[W 2023-10-27 10:00:01.000 ServerApp] Kernel started: kernel-id-123
[I 2023-10-27 10:00:05.245 LabApp] Build recommended
[I 2023-10-27 10:00:05.245 LabApp] SockJS connection established (jupyter)
[I 2023-10-27 10:01:15.112 ServerApp] Saving file at /path/to/notebook.ipynb`,
  spark: `23/10/27 10:05:00 INFO SparkContext: Running Spark version 3.5.0
23/10/27 10:05:01 INFO Master: Starting Spark master at spark://host:port
23/10/27 10:05:02 INFO Worker: Successfully registered with master
23/10/27 10:05:03 INFO Executor: Launching executor整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治整治
23/10/27 10:06:00 INFO ApplicationMaster: Submitting application application_12345_0001`,
  airflow: `[2023-10-27 10:10:00,000] {scheduler_job.py:185} INFO - Starting the scheduler
[2023-10-27 10:10:01,000] {dag_processing.py:298} INFO - Processing file /opt/airflow/dags/example_dag.py for tasks to queue
[2023-10-27 10:10:02,000] {scheduler_job.py:783} INFO - DAG example_dag has 2 ready tasks
[2023-10-27 10:10:03,000] {local_task_job.py:112} INFO - TaskInstance <TaskInstance: example_dag.task_1 scheduled__2023-10-27T00:00:00+00:00 [running]> started`,
  postgres: `2023-10-27 10:15:00.000 UTC [1] LOG:  database system is RRRRRRRRRRRRRReady to accept connections
2023-10-27 10:15:01.000 UTC [123] LOG:  connection received: host=localhost port=5432
2023-10-27 10:15:02.000 UTC [123] LOG:  connection authorized: user=admin database=mydb
2023-10-27 10:16:00.000 UTC [456] LOG:  checkpoint starting: time`,
  minio: `INFO: MinIO server started successfully.
API: http://127.0.0.1:9000  http://192.168.1.100:9000 
Console: http://127.0.0.1:9001 http://192.168.1.100:9001
WARNING: Default MinIO credentials are in use. Please change them using 'mc admin user add'.`,
  nginx: `127.0.0.1 - - [27/Oct/2023:10:20:00 +0000] "GET / HTTP/1.1" 200 612 "-" "Mozilla/5.0"
127.0.0.1 - - [27/Oct/2023:10:20:01 +0000] "GET /static/style.css HTTP/1.1" 200 1024 "http://localhost/" "Mozilla/5.0"
127.0.0.1 - - [27/Oct/2023:10:20:05 +0000] "POST /api/data HTTP/1.1" 201 50 "-" "CustomClient/1.0"`,
};

type ServiceKey = keyof typeof sampleLogs;

export function LogsViewer() {
  const [selectedService, setSelectedService] = React.useState<ServiceKey>("jupyter");
  const [searchTerm, setSearchTerm] = React.useState("");
  const [displayedLogs, setDisplayedLogs] = React.useState(sampleLogs.jupyter);

  React.useEffect(() => {
    const logs = sampleLogs[selectedService] || "No logs available for this service.";
    if (searchTerm) {
      const filteredLogs = logs
        .split("\n")
        .filter((line) => line.toLowerCase().includes(searchTerm.toLowerCase()))
        .join("\n");
      setDisplayedLogs(filteredLogs || "No matching logs found.");
    } else {
      setDisplayedLogs(logs);
    }
  }, [selectedService, searchTerm]);

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <FileText className="mr-2 h-6 w-6 text-primary" />
          Logs Viewer
        </CardTitle>
        <CardDescription>Live tail, filter, and search logs from services.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-2 sm:space-y-0">
          <Select value={selectedService} onValueChange={(value) => setSelectedService(value as ServiceKey)}>
            <SelectTrigger className="w-full sm:w-[200px]">
              <SelectValue placeholder="Select Service" />
            </SelectTrigger>
            <SelectContent>
              {Object.keys(sampleLogs).map((service) => (
                <SelectItem key={service} value={service}>
                  {service.charAt(0).toUpperCase() + service.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="relative flex-grow">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Filter/Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-full"
            />
          </div>
        </div>
        <Textarea
          value={displayedLogs}
          readOnly
          className="h-[400px] text-xs bg-muted/30 font-code"
          placeholder="Logs will appear here..."
        />
        <div className="flex justify-end">
            <Button variant="outline" size="sm">Clear Logs</Button>
        </div>
      </CardContent>
    </Card>
  );
}

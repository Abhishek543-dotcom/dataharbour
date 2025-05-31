"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BarChart3, Cpu, Database, HardDrive, Network } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface MetricItemProps {
  icon: React.ElementType;
  label: string;
  value: string | number;
  progress?: number;
  unit?: string;
}

function MetricItem({ icon: Icon, label, value, progress, unit }: MetricItemProps) {
  return (
    <div className="flex flex-col p-4 bg-card-foreground/5 rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center text-sm text-muted-foreground">
          <Icon className="h-4 w-4 mr-2" />
          {label}
        </div>
        <span className="text-lg font-semibold text-foreground">{value}{unit && <span className="text-xs text-muted-foreground ml-1">{unit}</span>}</span>
      </div>
      {progress !== undefined && <Progress value={progress} className="h-2 [&>div]:bg-primary" />}
    </div>
  );
}

export function MetricsPanel() {
  const [cpuUsage, setCpuUsage] = React.useState(0);
  const [ramUsage, setRamUsage] = React.useState(0);
  const [diskUsage, setDiskUsage] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setCpuUsage(Math.floor(Math.random() * 100));
      setRamUsage(Math.floor(Math.random() * 100));
      setDiskUsage(Math.floor(Math.random() * 100));
    }, 3000);
    return () => clearInterval(interval);
  }, []);


  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <BarChart3 className="mr-2 h-6 w-6 text-primary" />
          Metrics Panel
        </CardTitle>
        <CardDescription>System usage and Spark job performance statistics.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-md font-semibold mb-2 text-foreground/80">System Metrics</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <MetricItem icon={Cpu} label="CPU Usage" value={cpuUsage} progress={cpuUsage} unit="%" />
            <MetricItem icon={Database} label="RAM Usage" value={ramUsage} progress={ramUsage} unit="%" />
            <MetricItem icon={HardDrive} label="Disk Usage" value={diskUsage} progress={diskUsage} unit="%" />
            <MetricItem icon={Network} label="Network I/O" value="125.7" unit="MB/s" />
          </div>
        </div>
        <div>
          <h3 className="text-md font-semibold mb-2 text-foreground/80">Spark Job Performance</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <MetricItem icon={BarChart3} label="Active Jobs" value="5" />
            <MetricItem icon={BarChart3} label="Completed Stages" value="1,234" />
            <MetricItem icon={BarChart3} label="Avg. Task Time" value="2.5" unit="s" />
            <MetricItem icon={BarChart3} label="Shuffle Read/Write" value="1.2 / 0.8" unit="GB" />
          </div>
        </div>
         <div className="text-center text-xs text-muted-foreground pt-2">
            Metrics are simulated and update periodically.
        </div>
      </CardContent>
    </Card>
  );
}

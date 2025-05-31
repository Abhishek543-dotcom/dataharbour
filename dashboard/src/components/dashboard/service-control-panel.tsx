"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, StopCircle, RefreshCcw, Cpu, MemoryStick, Server } from "lucide-react";

interface Service {
  id: string;
  name: string;
  icon: React.ElementType;
  status: "running" | "stopped" | "degraded";
  cpuUsage: string;
  memoryUsage: string;
}

const initialServices: Service[] = [
  { id: "jupyter", name: "Jupyter", icon: Server, status: "running", cpuUsage: "15%", memoryUsage: "512MB / 2GB" },
  { id: "spark", name: "Spark Master", icon: Cpu, status: "running", cpuUsage: "30%", memoryUsage: "2GB / 8GB" },
  { id: "spark-worker-1", name: "Spark Worker 1", icon: Cpu, status: "running", cpuUsage: "25%", memoryUsage: "1.5GB / 4GB" },
  { id: "airflow", name: "Airflow", icon: Server, status: "degraded", cpuUsage: "5%", memoryUsage: "1GB / 4GB" },
  { id: "postgres", name: "PostgreSQL", icon: Server, status: "running", cpuUsage: "10%", memoryUsage: "256MB / 1GB" },
  { id: "minio", name: "MinIO", icon: Server, status: "stopped", cpuUsage: "0%", memoryUsage: "N/A" },
  { id: "nginx", name: "NGINX", icon: Server, status: "running", cpuUsage: "2%", memoryUsage: "128MB / 512MB" },
];

export function ServiceControlPanel() {
  const [services, setServices] = React.useState<Service[]>(initialServices);

  const getStatusColor = (status: Service["status"]) => {
    if (status === "running") return "bg-green-500";
    if (status === "stopped") return "bg-red-500";
    if (status === "degraded") return "bg-yellow-500";
    return "bg-gray-500";
  };

  const handleAction = (serviceId: string, action: "start" | "stop" | "restart") => {
    setServices(prevServices => 
      prevServices.map(service => {
        if (service.id === serviceId) {
          let newStatus: Service["status"] = service.status;
          if (action === "start") newStatus = "running";
          else if (action === "stop") newStatus = "stopped";
          else if (action === "restart") newStatus = "running"; // Simplified: assumes restart leads to running
          return { ...service, status: newStatus };
        }
        return service;
      })
    );
  };

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <Cpu className="mr-2 h-6 w-6 text-primary" />
          Service Control Panel
        </CardTitle>
        <CardDescription>Manage your data platform services.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service) => {
            const ServiceIcon = service.icon;
            return (
              <Card key={service.id} className="bg-card/50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                     <CardTitle className="text-lg font-medium flex items-center">
                       <ServiceIcon className="mr-2 h-5 w-5 text-muted-foreground" />
                       {service.name}
                     </CardTitle>
                    <Badge variant={service.status === 'running' ? 'default' : service.status === 'stopped' ? 'destructive' : 'secondary'}
                           className={`${getStatusColor(service.status)} text-primary-foreground px-2 py-0.5 text-xs`}>
                      {service.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-xs text-muted-foreground flex items-center">
                    <Cpu size={14} className="mr-1" /> CPU: {service.cpuUsage}
                  </div>
                  <div className="text-xs text-muted-foreground flex items-center">
                    <MemoryStick size={14} className="mr-1" /> Mem: {service.memoryUsage}
                  </div>
                  <div className="flex space-x-2 pt-2">
                    <Button variant="outline" size="sm" onClick={() => handleAction(service.id, "start")} disabled={service.status === "running"}>
                      <Play size={16} className="mr-1" /> Start
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => handleAction(service.id, "stop")} disabled={service.status === "stopped"}>
                      <StopCircle size={16} className="mr-1" /> Stop
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleAction(service.id, "restart")}>
                      <RefreshCcw size={16} className="mr-1" /> Restart
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

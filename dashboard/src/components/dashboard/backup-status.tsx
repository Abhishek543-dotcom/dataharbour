"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShieldCheck, RotateCcw, CalendarClock } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function BackupStatus() {
  const { toast } = useToast();
  const [lastBackup, setLastBackup] = React.useState<Date | null>(null);
  const [nextBackup, setNextBackup] = React.useState<Date | null>(null);

  React.useEffect(() => {
    // Simulate fetching backup times
    const now = new Date();
    setLastBackup(new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000)); // Random time in last 24h
    setNextBackup(new Date(now.getTime() + (6 * 60 * 60 * 1000) - (Math.random() * 60 * 60 * 1000))); // Approx 6h from now
  }, []);

  const handleRestore = () => {
    toast({
      title: "Restore Initiated",
      description: "Manual restore process has been started. This may take some time.",
      variant: "default",
    });
  };

  const formatDate = (date: Date | null) => {
    if (!date) return "N/A";
    return date.toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <ShieldCheck className="mr-2 h-6 w-6 text-primary" />
          Backup Status
        </CardTitle>
        <CardDescription>Monitor data backup and restore operations.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center p-3 bg-card-foreground/5 rounded-lg">
          <CalendarClock size={20} className="mr-3 text-accent" />
          <div>
            <p className="text-sm text-muted-foreground">Last Successful Backup</p>
            <p className="text-md font-semibold text-foreground">{formatDate(lastBackup)}</p>
          </div>
        </div>
        <div className="flex items-center p-3 bg-card-foreground/5 rounded-lg">
          <CalendarClock size={20} className="mr-3 text-accent" />
          <div>
            <p className="text-sm text-muted-foreground">Next Scheduled Backup</p>
            <p className="text-md font-semibold text-foreground">{formatDate(nextBackup)}</p>
          </div>
        </div>
        <Button onClick={handleRestore} className="w-full" variant="outline">
          <RotateCcw size={18} className="mr-2" />
          Manual Restore
        </Button>
      </CardContent>
    </Card>
  );
}

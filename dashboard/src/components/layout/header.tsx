
"use client";

import * as React from "react";
import { Ship, UserCircle, RefreshCw } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export function Header() {
  const [autoRefresh, setAutoRefresh] = React.useState(true);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 max-w-screen-2xl items-center">
        <div className="mr-4 flex items-center">
          <Ship className="h-7 w-7 mr-2 text-primary" />
          <h1 className="text-xl font-bold font-headline text-primary">DataHarbour</h1>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
              aria-label="Auto refresh"
            />
            <Label htmlFor="auto-refresh" className="text-sm text-muted-foreground">
              Auto-Refresh
            </Label>
          </div>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center space-x-2">
            <UserCircle className="h-6 w-6 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Jane Doe</span>
          </div>
           <Button variant="outline" size="sm">Logout</Button>
        </div>
      </div>
    </header>
  );
}

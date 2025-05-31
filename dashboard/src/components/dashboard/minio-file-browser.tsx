"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Folder, File, Download, Eye } from "lucide-react";

interface FileSystemItem {
  id: string;
  name: string;
  type: "folder" | "file";
  size?: string;
  lastModified?: string;
}

const sampleFiles: FileSystemItem[] = [
  { id: "1", name: "datasets", type: "folder" },
  { id: "2", name: "output_files", type: "folder" },
  { id: "3", name: "README.md", type: "file", size: "1.2KB", lastModified: "2023-10-26" },
];

export function MinioFileBrowser() {
  const [currentPath, setCurrentPath] = React.useState<string>("/");
  const [items, setItems] = React.useState<FileSystemItem[]>(sampleFiles);

  // In a real app, items would be fetched based on currentPath

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center font-headline">
          <Folder className="mr-2 h-6 w-6 text-primary" />
          MinIO File Browser
        </CardTitle>
        <CardDescription>Navigate datasets and output files stored in MinIO. (Optional Feature)</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 p-2 bg-muted/30 rounded-md text-sm text-muted-foreground">
          Current Path: {currentPath}
        </div>
        <div className="space-y-2 h-64 overflow-y-auto border p-2 rounded-md">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-2 hover:bg-muted/50 rounded-md">
              <div className="flex items-center">
                {item.type === "folder" ? <Folder size={18} className="mr-2 text-primary" /> : <File size={18} className="mr-2 text-muted-foreground" />}
                <span>{item.name}</span>
              </div>
              <div className="flex items-center space-x-2">
                {item.type === "file" && (
                  <>
                    <span className="text-xs text-muted-foreground">{item.size}</span>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <Eye size={16} />
                      <span className="sr-only">Preview</span>
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7">
                      <Download size={16} />
                      <span className="sr-only">Download</span>
                    </Button>
                  </>
                )}
                 {item.type === "folder" && (
                     <Button variant="link" size="sm" onClick={() => setCurrentPath(`${currentPath}${item.name}/`)}>Open</Button>
                 )}
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <div className="text-center text-muted-foreground py-8">This folder is empty.</div>
          )}
        </div>
        <div className="text-center text-xs text-muted-foreground pt-4">
          File browser functionality is a simplified placeholder.
        </div>
      </CardContent>
    </Card>
  );
}

"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Activity, Download, Eye, Pause, Play, Square, Terminal, TrendingUp } from "lucide-react"
import type { CloudJob } from "@/lib/cloud-providers"

interface CloudJobMonitorProps {
  job: CloudJob
  onPause: (jobId: string) => void
  onResume: (jobId: string) => void
  onCancel: (jobId: string) => void
  onDownload: (jobId: string) => void
}

export function CloudJobMonitor({ job, onPause, onResume, onCancel, onDownload }: CloudJobMonitorProps) {
  const [realTimeStats, setRealTimeStats] = useState({
    cpuUsage: 0,
    memoryUsage: 0,
    gpuUsage: 0,
    networkIO: 0,
    currentFrame: 0,
    framesPerMinute: 0,
    estimatedTimeRemaining: 0,
  })

  // Simulate real-time stats updates
  useEffect(() => {
    if (job.status === "rendering") {
      const interval = setInterval(() => {
        setRealTimeStats({
          cpuUsage: Math.random() * 100,
          memoryUsage: 60 + Math.random() * 30,
          gpuUsage: 80 + Math.random() * 20,
          networkIO: Math.random() * 50,
          currentFrame: job.frames.completed + Math.floor(Math.random() * 3),
          framesPerMinute: 2.5 + Math.random() * 1.5,
          estimatedTimeRemaining: Math.max(0, (job.frames.total - job.frames.completed) * 2),
        })
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [job.status, job.frames])

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = Math.floor(minutes % 60)
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  const getStatusColor = (status: CloudJob["status"]) => {
    switch (status) {
      case "completed":
        return "bg-green-500"
      case "failed":
      case "cancelled":
        return "bg-red-500"
      case "rendering":
      case "processing":
        return "bg-blue-500"
      case "starting":
        return "bg-yellow-500"
      default:
        return "bg-gray-500"
    }
  }

  return (
    <div className="space-y-6">
      {/* Job Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(job.status)}`} />
                {job.name}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Job ID: {job.id} • {job.provider.toUpperCase()} • {job.instanceType}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {job.status === "rendering" && (
                <Button variant="outline" size="sm" onClick={() => onPause(job.id)}>
                  <Pause className="w-4 h-4" />
                </Button>
              )}
              {job.status === "paused" && (
                <Button variant="outline" size="sm" onClick={() => onResume(job.id)}>
                  <Play className="w-4 h-4" />
                </Button>
              )}
              {job.status === "completed" && (
                <Button variant="outline" size="sm" onClick={() => onDownload(job.id)}>
                  <Download className="w-4 h-4" />
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={() => onCancel(job.id)}>
                <Square className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <Badge variant={job.status === "completed" ? "default" : "secondary"}>{job.status}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Progress</p>
              <p className="font-medium">{job.progress}%</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Frames</p>
              <p className="font-medium">
                {job.frames.completed}/{job.frames.total}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Cost</p>
              <p className="font-medium">
                ${job.actualCost?.toFixed(2) || job.estimatedCost.toFixed(2)}
                {!job.actualCost && " (est.)"}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{job.progress}%</span>
            </div>
            <Progress value={job.progress} className="w-full" />
          </div>
        </CardContent>
      </Card>

      {/* Detailed Monitoring */}
      <Tabs defaultValue="performance" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  System Resources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>CPU Usage</span>
                    <span>{realTimeStats.cpuUsage.toFixed(1)}%</span>
                  </div>
                  <Progress value={realTimeStats.cpuUsage} className="h-2" />
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Memory Usage</span>
                    <span>{realTimeStats.memoryUsage.toFixed(1)}%</span>
                  </div>
                  <Progress value={realTimeStats.memoryUsage} className="h-2" />
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>GPU Usage</span>
                    <span>{realTimeStats.gpuUsage.toFixed(1)}%</span>
                  </div>
                  <Progress value={realTimeStats.gpuUsage} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Render Statistics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Current Frame</span>
                  <span>{realTimeStats.currentFrame}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Frames/Minute</span>
                  <span>{realTimeStats.framesPerMinute.toFixed(1)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Time Remaining</span>
                  <span>{formatDuration(realTimeStats.estimatedTimeRemaining)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Failed Frames</span>
                  <span className={job.frames.failed > 0 ? "text-red-500" : ""}>{job.frames.failed}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Render Logs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64 w-full">
                <div className="space-y-2 font-mono text-xs">
                  {job.logs.map((log, index) => (
                    <div key={index} className="flex gap-2">
                      <span className="text-muted-foreground">{log.timestamp.toLocaleTimeString()}</span>
                      <span
                        className={
                          log.level === "error"
                            ? "text-red-500"
                            : log.level === "warning"
                              ? "text-yellow-500"
                              : "text-foreground"
                        }
                      >
                        [{log.level.toUpperCase()}]
                      </span>
                      <span>{log.message}</span>
                    </div>
                  ))}
                  {/* Simulate live logs */}
                  {job.status === "rendering" && (
                    <div className="flex gap-2 animate-pulse">
                      <span className="text-muted-foreground">{new Date().toLocaleTimeString()}</span>
                      <span className="text-foreground">[INFO]</span>
                      <span>Rendering frame {realTimeStats.currentFrame}...</span>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Eye className="w-4 h-4" />
                Render Preview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="aspect-video bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <Eye className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Latest rendered frame will appear here</p>
                  {job.status === "rendering" && (
                    <p className="text-xs mt-1">Frame {realTimeStats.currentFrame} rendering...</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Cost Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Compute Time</span>
                  <span>${((job.actualCost || job.estimatedCost) * 0.8).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Storage</span>
                  <span>${((job.actualCost || job.estimatedCost) * 0.1).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Data Transfer</span>
                  <span>${((job.actualCost || job.estimatedCost) * 0.1).toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-medium border-t pt-2">
                  <span>Total</span>
                  <span>${(job.actualCost || job.estimatedCost).toFixed(2)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Time Tracking</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Started</span>
                  <span>{job.startedAt?.toLocaleTimeString() || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Running Time</span>
                  <span>{job.startedAt ? formatDuration((Date.now() - job.startedAt.getTime()) / 60000) : "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Est. Completion</span>
                  <span>
                    {realTimeStats.estimatedTimeRemaining > 0
                      ? new Date(Date.now() + realTimeStats.estimatedTimeRemaining * 60000).toLocaleTimeString()
                      : "N/A"}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

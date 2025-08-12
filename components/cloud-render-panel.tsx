"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Cloud,
  Server,
  DollarSign,
  Clock,
  Zap,
  MapPin,
  Cpu,
  MemoryStick,
  Play,
  Pause,
  Square,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from "lucide-react"
import { cloudProviders, type CloudProvider, type InstanceType, type CloudJob } from "@/lib/cloud-providers"

interface CloudRenderPanelProps {
  onStartCloudRender: (config: CloudRenderConfig) => void
}

export interface CloudRenderConfig {
  provider: string
  region: string
  instanceType: string
  autoShutdown: boolean
  maxCost: number
}

export function CloudRenderPanel({ onStartCloudRender }: CloudRenderPanelProps) {
  const [selectedProvider, setSelectedProvider] = useState<CloudProvider | null>(null)
  const [selectedRegion, setSelectedRegion] = useState("")
  const [selectedInstanceType, setSelectedInstanceType] = useState<InstanceType | null>(null)
  const [estimatedCost, setEstimatedCost] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState(0)
  const [cloudJobs, setCloudJobs] = useState<CloudJob[]>([])
  const [totalSpent, setTotalSpent] = useState(0)

  // Mock cloud jobs for demonstration
  useEffect(() => {
    const mockJobs: CloudJob[] = [
      {
        id: "job-001",
        name: "Animation Sequence 01",
        status: "rendering",
        provider: "aws",
        region: "us-east-1",
        instanceType: "g4dn.xlarge",
        createdAt: new Date(Date.now() - 3600000),
        startedAt: new Date(Date.now() - 3000000),
        estimatedCost: 15.75,
        progress: 65,
        frames: { total: 250, completed: 162, failed: 0 },
        logs: [
          { timestamp: new Date(), level: "info", message: "Rendering frame 162/250" },
          { timestamp: new Date(Date.now() - 300000), level: "info", message: "Denoising completed" },
        ],
      },
      {
        id: "job-002",
        name: "Product Showcase",
        status: "completed",
        provider: "gcp",
        region: "us-central1",
        instanceType: "n1-standard-4-t4",
        createdAt: new Date(Date.now() - 7200000),
        startedAt: new Date(Date.now() - 6600000),
        completedAt: new Date(Date.now() - 1800000),
        estimatedCost: 8.4,
        actualCost: 7.85,
        progress: 100,
        frames: { total: 120, completed: 120, failed: 0 },
        logs: [{ timestamp: new Date(Date.now() - 1800000), level: "info", message: "Render completed successfully" }],
      },
    ]
    setCloudJobs(mockJobs)
    setTotalSpent(127.45)
  }, [])

  const calculateEstimates = () => {
    if (!selectedInstanceType) return

    // Mock calculation based on 250 frames, 2 minutes per frame
    const renderTimeHours = (250 * 2) / 60 / 60
    const cost = renderTimeHours * selectedInstanceType.pricePerHour
    const timeMinutes = 250 * 2

    setEstimatedCost(cost)
    setEstimatedTime(timeMinutes)
  }

  useEffect(() => {
    calculateEstimates()
  }, [selectedInstanceType])

  const handleProviderChange = (providerId: string) => {
    const provider = cloudProviders.find((p) => p.id === providerId)
    setSelectedProvider(provider || null)
    setSelectedRegion("")
    setSelectedInstanceType(null)
  }

  const handleInstanceTypeChange = (instanceTypeId: string) => {
    if (!selectedProvider) return
    const instanceType = selectedProvider.instanceTypes.find((it) => it.id === instanceTypeId)
    setSelectedInstanceType(instanceType || null)
  }

  const handleStartRender = () => {
    if (!selectedProvider || !selectedRegion || !selectedInstanceType) return

    const config: CloudRenderConfig = {
      provider: selectedProvider.id,
      region: selectedRegion,
      instanceType: selectedInstanceType.id,
      autoShutdown: true,
      maxCost: estimatedCost * 1.2, // 20% buffer
    }

    onStartCloudRender(config)
  }

  const getStatusIcon = (status: CloudJob["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "failed":
      case "cancelled":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "rendering":
      case "processing":
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Cloud Provider Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cloud className="w-5 h-5" />
            Cloud Rendering Setup
          </CardTitle>
          <CardDescription>Configure cloud instances for scalable rendering</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Cloud Provider</label>
            <Select onValueChange={handleProviderChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select cloud provider" />
              </SelectTrigger>
              <SelectContent>
                {cloudProviders.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id}>
                    {provider.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedProvider && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Region</label>
              <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                <SelectTrigger>
                  <SelectValue placeholder="Select region" />
                </SelectTrigger>
                <SelectContent>
                  {selectedProvider.regions.map((region) => (
                    <SelectItem key={region.id} value={region.id} disabled={!region.available}>
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        {region.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {selectedProvider && selectedRegion && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Instance Type</label>
              <Select onValueChange={handleInstanceTypeChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select instance type" />
                </SelectTrigger>
                <SelectContent>
                  {selectedProvider.instanceTypes.map((instanceType) => (
                    <SelectItem key={instanceType.id} value={instanceType.id}>
                      <div className="flex items-center justify-between w-full">
                        <div>
                          <div className="flex items-center gap-2">
                            {instanceType.recommended && <Badge variant="secondary">Recommended</Badge>}
                            <span className="font-medium">{instanceType.name}</span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                            <span className="flex items-center gap-1">
                              <Cpu className="w-3 h-3" />
                              {instanceType.cpu} vCPU
                            </span>
                            <span className="flex items-center gap-1">
                              <MemoryStick className="w-3 h-3" />
                              {instanceType.memory}GB RAM
                            </span>
                            {instanceType.gpu && (
                              <span className="flex items-center gap-1">
                                <Zap className="w-3 h-3" />
                                {instanceType.gpu.type}
                              </span>
                            )}
                          </div>
                        </div>
                        <span className="text-sm font-medium">${instanceType.pricePerHour}/hr</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cost Estimation */}
      {selectedInstanceType && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Cost Estimation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Estimated Cost</p>
                <p className="text-2xl font-bold text-green-600">${estimatedCost.toFixed(2)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Estimated Time</p>
                <p className="text-2xl font-bold text-blue-600">
                  {Math.round(estimatedTime / 60)}h {estimatedTime % 60}m
                </p>
              </div>
            </div>

            <Separator />

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Compute ({selectedInstanceType.pricePerHour}/hr)</span>
                <span>${(estimatedCost * 0.8).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Storage & Transfer</span>
                <span>${(estimatedCost * 0.15).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Processing Tools</span>
                <span>${(estimatedCost * 0.05).toFixed(2)}</span>
              </div>
            </div>

            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Actual costs may vary based on processing time and data transfer. A 20% buffer is recommended.
              </AlertDescription>
            </Alert>

            <Button onClick={handleStartRender} className="w-full" size="lg">
              <Play className="w-4 h-4 mr-2" />
              Start Cloud Render
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Active Jobs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Cloud Render Jobs
          </CardTitle>
          <CardDescription>Monitor your active and completed renders</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {cloudJobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Cloud className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No cloud render jobs yet</p>
            </div>
          ) : (
            cloudJobs.map((job) => (
              <div key={job.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(job.status)}
                    <span className="font-medium">{job.name}</span>
                    <Badge variant="outline">{job.status}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm">
                      <Pause className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Square className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Provider</p>
                    <p className="font-medium">{job.provider.toUpperCase()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Instance</p>
                    <p className="font-medium">{job.instanceType}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Cost</p>
                    <p className="font-medium">
                      ${job.actualCost?.toFixed(2) || job.estimatedCost.toFixed(2)}
                      {!job.actualCost && " (est.)"}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>
                      {job.frames.completed}/{job.frames.total} frames ({job.progress}%)
                    </span>
                  </div>
                  <Progress value={job.progress} className="w-full" />
                </div>

                {job.logs.length > 0 && (
                  <div className="text-xs text-muted-foreground">Latest: {job.logs[0].message}</div>
                )}
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Usage Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Usage Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Spent This Month</p>
              <p className="text-2xl font-bold">${totalSpent.toFixed(2)}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Active Jobs</p>
              <p className="text-2xl font-bold">{cloudJobs.filter((j) => j.status === "rendering").length}</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>AWS</span>
              <span>${(totalSpent * 0.6).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Google Cloud</span>
              <span>${(totalSpent * 0.3).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>Azure</span>
              <span>${(totalSpent * 0.1).toFixed(2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

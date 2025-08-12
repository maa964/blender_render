"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Play,
  Settings,
  ImageIcon,
  Video,
  Zap,
  Cpu,
  Monitor,
  FileVideo,
  Folder,
  Upload,
  CheckCircle,
  AlertCircle,
  Loader2,
  Cloud,
} from "lucide-react"

import { CloudRenderPanel, type CloudRenderConfig } from "@/components/cloud-render-panel"

type ProcessingStep =
  | "idle"
  | "rendering"
  | "denoising"
  | "upscaling"
  | "interpolating"
  | "encoding"
  | "complete"
  | "error"

interface RenderSettings {
  blenderPath: string
  blendFile: string
  outputDir: string
  frameStart: number
  frameEnd: number
  resolutionX: number
  resolutionY: number
  samples: number
  denoiseMethod: "OIDN" | "FastDVDnet"
  useCuda: boolean
  enableUpscale: boolean
  enableInterpolation: boolean
  codec: "prores_ks" | "qtrle"
  framerate: number
}

export default function BlenderRenderApp() {
  const [settings, setSettings] = useState<RenderSettings>({
    blenderPath: "",
    blendFile: "",
    outputDir: "",
    frameStart: 1,
    frameEnd: 250,
    resolutionX: 1920,
    resolutionY: 1080,
    samples: 128,
    denoiseMethod: "OIDN",
    useCuda: true,
    enableUpscale: false,
    enableInterpolation: false,
    codec: "prores_ks",
    framerate: 30,
  })

  const [currentStep, setCurrentStep] = useState<ProcessingStep>("idle")
  const [progress, setProgress] = useState(0)
  const [statusMessage, setStatusMessage] = useState("Ready to render")
  const [previewImage, setPreviewImage] = useState<string | null>(null)

  const [useCloudRender, setUseCloudRender] = useState(false)
  const [cloudConfig, setCloudConfig] = useState<CloudRenderConfig | null>(null)
  const [selectedCloudJob, setSelectedCloudJob] = useState<string | null>(null)

  const updateSetting = useCallback((key: keyof RenderSettings, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }, [])

  const simulateProcessing = async () => {
    const steps: { step: ProcessingStep; message: string; duration: number }[] = [
      { step: "rendering", message: "Rendering frames with Blender...", duration: 3000 },
      { step: "denoising", message: "Applying AI denoising...", duration: 2000 },
      ...(settings.enableUpscale
        ? [{ step: "upscaling" as ProcessingStep, message: "Upscaling with Real-ESRGAN...", duration: 2500 }]
        : []),
      ...(settings.enableInterpolation
        ? [{ step: "interpolating" as ProcessingStep, message: "Frame interpolation with RIFE...", duration: 2000 }]
        : []),
      { step: "encoding", message: "Encoding final video...", duration: 1500 },
      { step: "complete", message: "Rendering complete!", duration: 0 },
    ]

    for (const { step, message, duration } of steps) {
      setCurrentStep(step)
      setStatusMessage(message)

      if (duration > 0) {
        for (let i = 0; i <= 100; i += 2) {
          setProgress(i)
          await new Promise((resolve) => setTimeout(resolve, duration / 50))
        }
      }
    }
  }

  const handleStartRender = () => {
    if (!settings.blenderPath || !settings.blendFile || !settings.outputDir) {
      setCurrentStep("error")
      setStatusMessage("Please configure all required paths")
      return
    }
    simulateProcessing()
  }

  const handleStartCloudRender = (config: CloudRenderConfig) => {
    setCloudConfig(config)
    setUseCloudRender(true)
    // Here you would integrate with actual cloud APIs
    setStatusMessage(`Starting cloud render on ${config.provider}...`)
    simulateProcessing()
  }

  const handleCloudJobAction = (action: string, jobId: string) => {
    setStatusMessage(`${action} job ${jobId}`)
  }

  const getStepIcon = (step: ProcessingStep) => {
    switch (step) {
      case "rendering":
        return <Monitor className="w-4 h-4" />
      case "denoising":
        return <Zap className="w-4 h-4" />
      case "upscaling":
        return <ImageIcon className="w-4 h-4" />
      case "interpolating":
        return <Video className="w-4 h-4" />
      case "encoding":
        return <FileVideo className="w-4 h-4" />
      case "complete":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Settings className="w-4 h-4" />
    }
  }

  const isProcessing = ["rendering", "denoising", "upscaling", "interpolating", "encoding"].includes(currentStep)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Blender Render Pipeline
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Professional 3D rendering with AI enhancement and post-processing
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Panel */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic Settings</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
                <TabsTrigger value="output">Output</TabsTrigger>
                <TabsTrigger value="cloud">Cloud Render</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Folder className="w-5 h-5" />
                      File Paths
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="blender-path">Blender Executable</Label>
                      <div className="flex gap-2">
                        <Input
                          id="blender-path"
                          placeholder="C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
                          value={settings.blenderPath}
                          onChange={(e) => updateSetting("blenderPath", e.target.value)}
                        />
                        <Button variant="outline" size="icon">
                          <Upload className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="blend-file">Blend File</Label>
                      <div className="flex gap-2">
                        <Input
                          id="blend-file"
                          placeholder="Select your .blend file"
                          value={settings.blendFile}
                          onChange={(e) => updateSetting("blendFile", e.target.value)}
                        />
                        <Button variant="outline" size="icon">
                          <Upload className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="output-dir">Output Directory</Label>
                      <div className="flex gap-2">
                        <Input
                          id="output-dir"
                          placeholder="Choose output folder"
                          value={settings.outputDir}
                          onChange={(e) => updateSetting("outputDir", e.target.value)}
                        />
                        <Button variant="outline" size="icon">
                          <Folder className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Settings className="w-5 h-5" />
                      Render Settings
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="frame-start">Start Frame</Label>
                        <Input
                          id="frame-start"
                          type="number"
                          value={settings.frameStart}
                          onChange={(e) => updateSetting("frameStart", Number.parseInt(e.target.value))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="frame-end">End Frame</Label>
                        <Input
                          id="frame-end"
                          type="number"
                          value={settings.frameEnd}
                          onChange={(e) => updateSetting("frameEnd", Number.parseInt(e.target.value))}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="res-x">Width</Label>
                        <Input
                          id="res-x"
                          type="number"
                          value={settings.resolutionX}
                          onChange={(e) => updateSetting("resolutionX", Number.parseInt(e.target.value))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="res-y">Height</Label>
                        <Input
                          id="res-y"
                          type="number"
                          value={settings.resolutionY}
                          onChange={(e) => updateSetting("resolutionY", Number.parseInt(e.target.value))}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="samples">Samples</Label>
                      <Input
                        id="samples"
                        type="number"
                        value={settings.samples}
                        onChange={(e) => updateSetting("samples", Number.parseInt(e.target.value))}
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="advanced" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="w-5 h-5" />
                      AI Enhancement
                    </CardTitle>
                    <CardDescription>Configure AI-powered post-processing options</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Denoising Method</Label>
                      <Select
                        value={settings.denoiseMethod}
                        onValueChange={(value: "OIDN" | "FastDVDnet") => updateSetting("denoiseMethod", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="OIDN">Intel Open Image Denoise</SelectItem>
                          <SelectItem value="FastDVDnet">FastDVDnet</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>CUDA Acceleration</Label>
                        <p className="text-sm text-muted-foreground">Use GPU for faster processing</p>
                      </div>
                      <Switch
                        checked={settings.useCuda}
                        onCheckedChange={(checked) => updateSetting("useCuda", checked)}
                      />
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>AI Upscaling</Label>
                        <p className="text-sm text-muted-foreground">Enhance resolution with Real-ESRGAN</p>
                      </div>
                      <Switch
                        checked={settings.enableUpscale}
                        onCheckedChange={(checked) => updateSetting("enableUpscale", checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Frame Interpolation</Label>
                        <p className="text-sm text-muted-foreground">Smooth motion with RIFE</p>
                      </div>
                      <Switch
                        checked={settings.enableInterpolation}
                        onCheckedChange={(checked) => updateSetting("enableInterpolation", checked)}
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="output" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileVideo className="w-5 h-5" />
                      Video Output
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Codec</Label>
                      <Select
                        value={settings.codec}
                        onValueChange={(value: "prores_ks" | "qtrle") => updateSetting("codec", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="prores_ks">ProRes 4444 (High Quality)</SelectItem>
                          <SelectItem value="qtrle">QuickTime RLE (Lossless)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Frame Rate</Label>
                      <Select
                        value={settings.framerate.toString()}
                        onValueChange={(value) => updateSetting("framerate", Number.parseInt(value))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="24">24 FPS (Cinema)</SelectItem>
                          <SelectItem value="30">30 FPS (Standard)</SelectItem>
                          <SelectItem value="60">60 FPS (Smooth)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="cloud" className="space-y-4">
                <CloudRenderPanel onStartCloudRender={handleStartCloudRender} />
              </TabsContent>
            </Tabs>
          </div>

          {/* Status Panel */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {getStepIcon(currentStep)}
                  Render Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Current Step:</span>
                  <Badge
                    variant={
                      currentStep === "complete" ? "default" : currentStep === "error" ? "destructive" : "secondary"
                    }
                  >
                    {currentStep === "idle" ? "Ready" : currentStep}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Progress</span>
                    <span>{progress}%</span>
                  </div>
                  <Progress value={progress} className="w-full" />
                </div>

                <p className="text-sm text-muted-foreground">{statusMessage}</p>

                <div className="flex gap-2">
                  <Button onClick={handleStartRender} disabled={isProcessing} className="flex-1" size="lg">
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        {useCloudRender ? "Start Cloud Render" : "Start Local Render"}
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={() => setUseCloudRender(!useCloudRender)} size="lg">
                    <Cloud className="w-4 h-4 mr-2" />
                    {useCloudRender ? "Local" : "Cloud"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Preview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="aspect-video bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
                  {previewImage ? (
                    <img
                      src={previewImage || "/placeholder.svg"}
                      alt="Preview"
                      className="max-w-full max-h-full rounded-lg"
                    />
                  ) : (
                    <div className="text-center text-muted-foreground">
                      <ImageIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">Preview will appear here</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="w-5 h-5" />
                  System Info
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>CUDA Available:</span>
                  <Badge variant={settings.useCuda ? "default" : "secondary"}>{settings.useCuda ? "Yes" : "No"}</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Total Frames:</span>
                  <span>{settings.frameEnd - settings.frameStart + 1}</span>
                </div>
                <div className="flex justify-between">
                  <span>Resolution:</span>
                  <span>
                    {settings.resolutionX}×{settings.resolutionY}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

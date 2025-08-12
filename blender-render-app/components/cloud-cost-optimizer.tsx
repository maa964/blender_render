"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { TrendingDown, TrendingUp, AlertTriangle, CheckCircle, BarChart3 } from "lucide-react"
import { cloudProviders } from "@/lib/cloud-providers"

interface CostOptimization {
  provider: string
  instanceType: string
  region: string
  estimatedCost: number
  estimatedTime: number
  savings: number
  recommendation: string
  pros: string[]
  cons: string[]
}

interface CloudCostOptimizerProps {
  frameCount: number
  resolution: [number, number]
  samples: number
  enableUpscale: boolean
  enableInterpolation: boolean
  onOptimizationSelect: (optimization: CostOptimization) => void
}

export function CloudCostOptimizer({
  frameCount,
  resolution,
  samples,
  enableUpscale,
  enableInterpolation,
  onOptimizationSelect,
}: CloudCostOptimizerProps) {
  const [optimizations, setOptimizations] = useState<CostOptimization[]>([])
  const [selectedOptimization, setSelectedOptimization] = useState<CostOptimization | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const calculateRenderComplexity = () => {
    const baseComplexity = (frameCount * (resolution[0] * resolution[1])) / 1000000
    const sampleMultiplier = samples / 128
    const upscaleMultiplier = enableUpscale ? 2.5 : 1
    const interpolationMultiplier = enableInterpolation ? 1.8 : 1

    return baseComplexity * sampleMultiplier * upscaleMultiplier * interpolationMultiplier
  }

  const generateOptimizations = () => {
    setIsAnalyzing(true)

    setTimeout(() => {
      const complexity = calculateRenderComplexity()
      const optimizations: CostOptimization[] = []

      cloudProviders.forEach((provider) => {
        provider.instanceTypes.forEach((instanceType) => {
          provider.regions.forEach((region) => {
            if (!region.available) return

            // Calculate estimated render time based on instance performance
            const performanceScore = instanceType.gpu
              ? instanceType.gpu.memory * instanceType.gpu.count + instanceType.cpu * 0.1
              : instanceType.cpu * 0.5

            const estimatedHours = complexity / performanceScore
            const estimatedCost = estimatedHours * instanceType.pricePerHour

            // Add storage and transfer costs
            const storageCost = frameCount * 0.01 * provider.pricing.storagePerGB
            const transferCost = frameCount * 0.05 * provider.pricing.dataTransferPerGB
            const totalCost = estimatedCost + storageCost + transferCost

            optimizations.push({
              provider: provider.id,
              instanceType: instanceType.id,
              region: region.id,
              estimatedCost: totalCost,
              estimatedTime: estimatedHours * 60, // Convert to minutes
              savings: 0, // Will be calculated relative to baseline
              recommendation: instanceType.recommended
                ? "Recommended"
                : totalCost < 20
                  ? "Budget-friendly"
                  : estimatedHours < 2
                    ? "Fast"
                    : "Standard",
              pros: [
                instanceType.gpu ? `Powerful ${instanceType.gpu.type} GPU` : "CPU-optimized",
                `${instanceType.cpu} vCPU cores`,
                `${instanceType.memory}GB RAM`,
                region.location,
              ],
              cons: [
                totalCost > 50 ? "Higher cost" : null,
                estimatedHours > 5 ? "Longer render time" : null,
                !instanceType.gpu ? "No GPU acceleration" : null,
              ].filter(Boolean) as string[],
            })
          })
        })
      })

      // Sort by cost and calculate savings
      optimizations.sort((a, b) => a.estimatedCost - b.estimatedCost)
      const baseline = optimizations[Math.floor(optimizations.length / 2)]?.estimatedCost || 0

      optimizations.forEach((opt) => {
        opt.savings = baseline - opt.estimatedCost
      })

      setOptimizations(optimizations.slice(0, 8)) // Show top 8 options
      setIsAnalyzing(false)
    }, 2000)
  }

  useEffect(() => {
    if (frameCount > 0) {
      generateOptimizations()
    }
  }, [frameCount, resolution, samples, enableUpscale, enableInterpolation])

  const handleSelectOptimization = (optimization: CostOptimization) => {
    setSelectedOptimization(optimization)
    onOptimizationSelect(optimization)
  }

  const getProviderName = (providerId: string) => {
    return cloudProviders.find((p) => p.id === providerId)?.name || providerId
  }

  const getInstanceTypeName = (providerId: string, instanceTypeId: string) => {
    const provider = cloudProviders.find((p) => p.id === providerId)
    return provider?.instanceTypes.find((it) => it.id === instanceTypeId)?.name || instanceTypeId
  }

  const getRegionName = (providerId: string, regionId: string) => {
    const provider = cloudProviders.find((p) => p.id === providerId)
    return provider?.regions.find((r) => r.id === regionId)?.name || regionId
  }

  if (isAnalyzing) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Cost Optimization Analysis
          </CardTitle>
          <CardDescription>Analyzing the best cloud options for your render...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span className="text-sm">Calculating optimal configurations...</span>
          </div>
          <Progress value={66} className="w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Cost Optimization Recommendations
          </CardTitle>
          <CardDescription>
            Based on your render settings: {frameCount} frames, {resolution[0]}×{resolution[1]}, {samples} samples
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert className="mb-4">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Found {optimizations.length} optimized configurations. Potential savings up to $
              {Math.max(...optimizations.map((o) => o.savings)).toFixed(2)}.
            </AlertDescription>
          </Alert>

          <div className="grid gap-4">
            {optimizations.map((opt, index) => (
              <div
                key={`${opt.provider}-${opt.instanceType}-${opt.region}`}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedOptimization === opt
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
                    : "hover:bg-gray-50 dark:hover:bg-gray-800"
                }`}
                onClick={() => handleSelectOptimization(opt)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={index === 0 ? "default" : "secondary"}>
                      {index === 0 ? "Best Value" : opt.recommendation}
                    </Badge>
                    <span className="font-medium">
                      {getProviderName(opt.provider)} - {getInstanceTypeName(opt.provider, opt.instanceType)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">${opt.estimatedCost.toFixed(2)}</p>
                      {opt.savings > 0 && (
                        <p className="text-xs text-green-600 flex items-center gap-1">
                          <TrendingDown className="w-3 h-3" />
                          Save ${opt.savings.toFixed(2)}
                        </p>
                      )}
                      {opt.savings < 0 && (
                        <p className="text-xs text-red-600 flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          +${Math.abs(opt.savings).toFixed(2)}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {Math.round(opt.estimatedTime / 60)}h {Math.round(opt.estimatedTime % 60)}m
                      </p>
                      <p className="text-xs text-muted-foreground">Est. time</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground mb-1">Advantages:</p>
                    <ul className="space-y-1">
                      {opt.pros.slice(0, 2).map((pro, i) => (
                        <li key={i} className="flex items-center gap-1 text-green-600">
                          <CheckCircle className="w-3 h-3" />
                          {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Considerations:</p>
                    <ul className="space-y-1">
                      {opt.cons.slice(0, 2).map((con, i) => (
                        <li key={i} className="flex items-center gap-1 text-yellow-600">
                          <AlertTriangle className="w-3 h-3" />
                          {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mt-2 text-xs text-muted-foreground">
                  Region: {getRegionName(opt.provider, opt.region)}
                </div>
              </div>
            ))}
          </div>

          {selectedOptimization && (
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <h4 className="font-medium mb-2">Selected Configuration</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Provider:</span>
                  <p className="font-medium">{getProviderName(selectedOptimization.provider)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Instance:</span>
                  <p className="font-medium">
                    {getInstanceTypeName(selectedOptimization.provider, selectedOptimization.instanceType)}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Region:</span>
                  <p className="font-medium">
                    {getRegionName(selectedOptimization.provider, selectedOptimization.region)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

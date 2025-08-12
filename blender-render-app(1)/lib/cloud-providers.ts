export interface CloudProvider {
  id: string
  name: string
  regions: CloudRegion[]
  instanceTypes: InstanceType[]
  pricing: PricingInfo
}

export interface CloudRegion {
  id: string
  name: string
  location: string
  available: boolean
}

export interface InstanceType {
  id: string
  name: string
  cpu: number
  memory: number
  gpu?: {
    type: string
    count: number
    memory: number
  }
  storage: number
  pricePerHour: number
  recommended?: boolean
}

export interface PricingInfo {
  computePerHour: number
  storagePerGB: number
  dataTransferPerGB: number
  currency: string
}

export interface CloudJob {
  id: string
  name: string
  status: "queued" | "starting" | "rendering" | "processing" | "completed" | "failed" | "cancelled"
  provider: string
  region: string
  instanceType: string
  createdAt: Date
  startedAt?: Date
  completedAt?: Date
  estimatedCost: number
  actualCost?: number
  progress: number
  frames: {
    total: number
    completed: number
    failed: number
  }
  logs: CloudJobLog[]
}

export interface CloudJobLog {
  timestamp: Date
  level: "info" | "warning" | "error"
  message: string
  details?: any
}

export const cloudProviders: CloudProvider[] = [
  {
    id: "aws",
    name: "Amazon Web Services",
    regions: [
      { id: "us-east-1", name: "US East (N. Virginia)", location: "Virginia, USA", available: true },
      { id: "us-west-2", name: "US West (Oregon)", location: "Oregon, USA", available: true },
      { id: "eu-west-1", name: "Europe (Ireland)", location: "Dublin, Ireland", available: true },
      { id: "ap-northeast-1", name: "Asia Pacific (Tokyo)", location: "Tokyo, Japan", available: true },
    ],
    instanceTypes: [
      {
        id: "g4dn.xlarge",
        name: "G4dn XLarge",
        cpu: 4,
        memory: 16,
        gpu: { type: "NVIDIA T4", count: 1, memory: 16 },
        storage: 125,
        pricePerHour: 0.526,
        recommended: true,
      },
      {
        id: "g4dn.2xlarge",
        name: "G4dn 2XLarge",
        cpu: 8,
        memory: 32,
        gpu: { type: "NVIDIA T4", count: 1, memory: 16 },
        storage: 225,
        pricePerHour: 0.752,
      },
      {
        id: "g5.xlarge",
        name: "G5 XLarge",
        cpu: 4,
        memory: 16,
        gpu: { type: "NVIDIA A10G", count: 1, memory: 24 },
        storage: 250,
        pricePerHour: 1.006,
      },
      {
        id: "g5.2xlarge",
        name: "G5 2XLarge",
        cpu: 8,
        memory: 32,
        gpu: { type: "NVIDIA A10G", count: 1, memory: 24 },
        storage: 450,
        pricePerHour: 1.212,
      },
    ],
    pricing: {
      computePerHour: 0.526,
      storagePerGB: 0.1,
      dataTransferPerGB: 0.09,
      currency: "USD",
    },
  },
  {
    id: "gcp",
    name: "Google Cloud Platform",
    regions: [
      { id: "us-central1", name: "US Central (Iowa)", location: "Iowa, USA", available: true },
      { id: "us-west1", name: "US West (Oregon)", location: "Oregon, USA", available: true },
      { id: "europe-west1", name: "Europe West (Belgium)", location: "Belgium", available: true },
      { id: "asia-east1", name: "Asia East (Taiwan)", location: "Taiwan", available: true },
    ],
    instanceTypes: [
      {
        id: "n1-standard-4-t4",
        name: "N1 Standard 4 + T4",
        cpu: 4,
        memory: 15,
        gpu: { type: "NVIDIA T4", count: 1, memory: 16 },
        storage: 100,
        pricePerHour: 0.35,
        recommended: true,
      },
      {
        id: "n1-standard-8-t4",
        name: "N1 Standard 8 + T4",
        cpu: 8,
        memory: 30,
        gpu: { type: "NVIDIA T4", count: 1, memory: 16 },
        storage: 100,
        pricePerHour: 0.55,
      },
      {
        id: "a2-highgpu-1g",
        name: "A2 High GPU 1G",
        cpu: 12,
        memory: 85,
        gpu: { type: "NVIDIA A100", count: 1, memory: 40 },
        storage: 100,
        pricePerHour: 3.673,
      },
    ],
    pricing: {
      computePerHour: 0.35,
      storagePerGB: 0.04,
      dataTransferPerGB: 0.12,
      currency: "USD",
    },
  },
  {
    id: "azure",
    name: "Microsoft Azure",
    regions: [
      { id: "eastus", name: "East US", location: "Virginia, USA", available: true },
      { id: "westus2", name: "West US 2", location: "Washington, USA", available: true },
      { id: "westeurope", name: "West Europe", location: "Netherlands", available: true },
      { id: "southeastasia", name: "Southeast Asia", location: "Singapore", available: true },
    ],
    instanceTypes: [
      {
        id: "Standard_NC6s_v3",
        name: "NC6s v3",
        cpu: 6,
        memory: 112,
        gpu: { type: "NVIDIA V100", count: 1, memory: 16 },
        storage: 736,
        pricePerHour: 3.06,
      },
      {
        id: "Standard_NC12s_v3",
        name: "NC12s v3",
        cpu: 12,
        memory: 224,
        gpu: { type: "NVIDIA V100", count: 2, memory: 32 },
        storage: 1474,
        pricePerHour: 6.12,
        recommended: true,
      },
    ],
    pricing: {
      computePerHour: 3.06,
      storagePerGB: 0.05,
      dataTransferPerGB: 0.087,
      currency: "USD",
    },
  },
]

/**
 * Hub Route
 *
 * Displays all Phlo services with their status and controls.
 */

import { createFileRoute, useRouter } from '@tanstack/react-router'
import { Boxes, CheckCircle, Loader2, RefreshCw, XCircle } from 'lucide-react'
import { useState } from 'react'

import type { ServiceWithStatus } from '@/server/services.server'
import { ServiceCard } from '@/components/hub/ServiceCard'
import {
  getServices,
  restartService,
  startService,
  stopService,
} from '@/server/services.server'

export const Route = createFileRoute('/hub/')({
  loader: async () => {
    const services = await getServices()
    return { services }
  },
  component: HubPage,
})

function HubPage() {
  const { services } = Route.useLoaderData()
  const router = useRouter()
  const [loadingServices, setLoadingServices] = useState<Set<string>>(new Set())

  // Group services by category
  const servicesByCategory = services.reduce(
    (acc, service) => {
      const cat = service.category
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(service)
      return acc
    },
    {} as Record<string, Array<ServiceWithStatus>>,
  )

  // Category order
  const categoryOrder = [
    'core',
    'orchestration',
    'api',
    'bi',
    'observability',
    'admin',
  ]
  const sortedCategories = Object.keys(servicesByCategory).sort(
    (a, b) => categoryOrder.indexOf(a) - categoryOrder.indexOf(b),
  )

  // Stats
  const totalServices = services.length
  const runningServices = services.filter(
    (s) => s.containerStatus?.status === 'running',
  ).length
  const stoppedServices = services.filter(
    (s) => !s.containerStatus || s.containerStatus.status === 'stopped',
  ).length
  const unhealthyServices = services.filter(
    (s) => s.containerStatus?.status === 'unhealthy',
  ).length

  const handleStart = async (name: string) => {
    setLoadingServices((prev) => new Set(prev).add(name))
    try {
      await startService({ data: name })
      // Refresh after a short delay to allow Docker to update
      setTimeout(() => router.invalidate(), 1000)
    } finally {
      setLoadingServices((prev) => {
        const next = new Set(prev)
        next.delete(name)
        return next
      })
    }
  }

  const handleStop = async (name: string) => {
    setLoadingServices((prev) => new Set(prev).add(name))
    try {
      await stopService({ data: name })
      setTimeout(() => router.invalidate(), 1000)
    } finally {
      setLoadingServices((prev) => {
        const next = new Set(prev)
        next.delete(name)
        return next
      })
    }
  }

  const handleRestart = async (name: string) => {
    setLoadingServices((prev) => new Set(prev).add(name))
    try {
      await restartService({ data: name })
      setTimeout(() => router.invalidate(), 2000)
    } finally {
      setLoadingServices((prev) => {
        const next = new Set(prev)
        next.delete(name)
        return next
      })
    }
  }

  const handleRefresh = () => {
    router.invalidate()
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Boxes className="w-8 h-8 text-cyan-400" />
            <h1 className="text-3xl font-bold">Service Hub</h1>
          </div>
          <p className="text-slate-400">
            Manage and monitor all Phlo platform services
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Services"
          value={totalServices}
          icon={<Boxes className="w-5 h-5" />}
        />
        <StatCard
          label="Running"
          value={runningServices}
          icon={<CheckCircle className="w-5 h-5" />}
          color="text-green-400"
        />
        <StatCard
          label="Stopped"
          value={stoppedServices}
          icon={<Loader2 className="w-5 h-5" />}
          color="text-slate-400"
        />
        <StatCard
          label="Unhealthy"
          value={unhealthyServices}
          icon={<XCircle className="w-5 h-5" />}
          color="text-red-400"
        />
      </div>

      {/* Services by Category */}
      {sortedCategories.map((category) => (
        <div key={category} className="mb-8">
          <h2 className="text-xl font-semibold mb-4 capitalize text-slate-200">
            {category}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {servicesByCategory[category].map((service) => (
              <ServiceCard
                key={service.name}
                service={service}
                onStart={handleStart}
                onStop={handleStop}
                onRestart={handleRestart}
                isLoading={loadingServices.has(service.name)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number
  icon: React.ReactNode
  color?: string
}

function StatCard({
  label,
  value,
  icon,
  color = 'text-cyan-400',
}: StatCardProps) {
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400">{label}</span>
        <div className={color}>{icon}</div>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}

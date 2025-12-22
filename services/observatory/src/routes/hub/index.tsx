/**
 * Hub Route
 *
 * Displays all Phlo services with their status and controls.
 */

import { createFileRoute, Link, useRouter } from '@tanstack/react-router'
import { Boxes, CheckCircle, Loader2, RefreshCw, XCircle } from 'lucide-react'
import { useState } from 'react'

import type { ServiceWithStatus } from '@/server/services.server'
import { ServiceCard } from '@/components/hub/ServiceCard'
import { buttonVariants, Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  getServices,
  restartService,
  startService,
  stopService,
} from '@/server/services.server'
import { cn } from '@/lib/utils'

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
      await startService({ data: { serviceName: name } })
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
      await stopService({ data: { serviceName: name } })
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
      await restartService({ data: { serviceName: name } })
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
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Boxes className="size-7 text-primary" />
              <h1 className="text-3xl font-bold">Service Hub</h1>
            </div>
            <p className="text-muted-foreground">
              Manage and monitor all Phlo platform services
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/hub/plugins"
              className={cn(buttonVariants({ variant: 'outline' }))}
            >
              Plugins
            </Link>
            <Button variant="outline" onClick={handleRefresh}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
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
            color="text-muted-foreground"
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
            <h2 className="text-xl font-semibold mb-4 capitalize">
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
  color = 'text-primary',
}: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center justify-between gap-2">
          <span>{label}</span>
          <span className={color}>{icon}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardContent>
    </Card>
  )
}

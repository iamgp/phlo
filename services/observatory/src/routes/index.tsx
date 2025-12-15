import { createFileRoute, useRouter } from '@tanstack/react-router'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react'
import type { ReactNode } from 'react'
import type {
  DagsterConnectionStatus,
  HealthMetrics,
} from '@/server/dagster.server'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  checkDagsterConnection,
  getHealthMetrics,
} from '@/server/dagster.server'

export const Route = createFileRoute('/')({
  loader: async () => {
    // Check connection and fetch metrics in parallel
    const [connection, metrics] = await Promise.all([
      checkDagsterConnection(),
      getHealthMetrics(),
    ])
    return { connection, metrics }
  },
  component: Dashboard,
})

function Dashboard() {
  const { connection, metrics } = Route.useLoaderData()
  const router = useRouter()

  const hasError = 'error' in metrics
  const healthData = hasError ? null : metrics

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold">Platform Health</h1>
            <p className="text-muted-foreground">
              Overview of your data platform status
            </p>
          </div>
          <Button variant="outline" onClick={() => router.invalidate()}>
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        </div>

        {/* Connection Status Banner */}
        <ConnectionBanner connection={connection} />

        {/* Health Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <HealthCard
            title="Assets"
            value={healthData?.assetsTotal?.toString() ?? '--'}
            subtitle={
              healthData
                ? `${healthData.assetsHealthy} healthy`
                : 'Total registered'
            }
            icon={<Database className="w-6 h-6" />}
            status={getAssetStatus(healthData)}
          />
          <HealthCard
            title="Failed Jobs"
            value={healthData?.failedJobs24h?.toString() ?? '--'}
            subtitle="Last 24 hours"
            icon={<AlertTriangle className="w-6 h-6" />}
            status={getFailedJobsStatus(healthData)}
          />
          <HealthCard
            title="Quality Checks"
            value={
              healthData
                ? `${healthData.qualityChecksPassing}/${healthData.qualityChecksTotal}`
                : '--'
            }
            subtitle="Passing"
            icon={<CheckCircle className="w-6 h-6" />}
            status={getQualityStatus(healthData)}
          />
          <HealthCard
            title="Freshness"
            value={
              healthData
                ? `${healthData.assetsTotal - healthData.staleAssets}/${healthData.assetsTotal}`
                : '--'
            }
            subtitle="Assets up to date"
            icon={<Clock className="w-6 h-6" />}
            status={getFreshnessStatus(healthData)}
          />
        </div>

        {/* Placeholder Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PlaceholderSection
            title="Recent Activity"
            description="Pipeline runs and data changes will appear here"
          />
          <PlaceholderSection
            title="Attention Needed"
            description="Failures, stale data, and quality issues will appear here"
          />
        </div>

        {/* Last Updated */}
        {healthData && (
          <div className="mt-6 text-sm text-muted-foreground text-right">
            Last updated: {new Date(healthData.lastUpdated).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  )
}

function ConnectionBanner({
  connection,
}: {
  connection: DagsterConnectionStatus
}) {
  if (connection.connected) {
    return (
      <Card className="mb-6 border-green-500/30 bg-green-500/5">
        <CardContent className="p-4 flex items-center gap-3">
          <Wifi className="size-5 text-green-400" />
          <span className="text-green-300">
            Connected to Dagster
            {connection.version ? ` (v${connection.version})` : ''}
          </span>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="mb-6 border-yellow-500/30 bg-yellow-500/5">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <WifiOff className="size-5 text-yellow-400" />
          <span className="text-yellow-300">Cannot connect to Dagster</span>
        </div>
        {connection.error && (
          <p className="mt-2 text-sm text-yellow-400/80">{connection.error}</p>
        )}
        <p className="mt-2 text-sm text-muted-foreground">
          Make sure Dagster is running:{' '}
          <code className="px-2 py-0.5 bg-muted rounded">
            docker compose up dagster-webserver
          </code>
        </p>
      </CardContent>
    </Card>
  )
}

// Status helper functions
function getAssetStatus(
  data: HealthMetrics | null,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.assetsTotal === 0) return 'warning'
  return 'success'
}

function getFailedJobsStatus(
  data: HealthMetrics | null,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.failedJobs24h === 0) return 'success'
  if (data.failedJobs24h <= 2) return 'warning'
  return 'error'
}

function getQualityStatus(
  data: HealthMetrics | null,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.qualityChecksTotal === 0) return 'loading' // Not implemented yet
  const ratio = data.qualityChecksPassing / data.qualityChecksTotal
  if (ratio === 1) return 'success'
  if (ratio >= 0.9) return 'warning'
  return 'error'
}

function getFreshnessStatus(
  data: HealthMetrics | null,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.assetsTotal === 0) return 'loading'
  const staleRatio = data.staleAssets / data.assetsTotal
  if (staleRatio === 0) return 'success'
  if (staleRatio <= 0.1) return 'warning'
  return 'error'
}

interface HealthCardProps {
  title: string
  value: string
  subtitle: string
  icon: ReactNode
  status: 'success' | 'warning' | 'error' | 'loading'
}

function HealthCard({ title, value, subtitle, icon, status }: HealthCardProps) {
  const statusColors = {
    success: 'text-green-400 bg-green-500/10',
    warning: 'text-yellow-400 bg-yellow-500/10',
    error: 'text-red-400 bg-red-500/10',
    loading: 'text-muted-foreground bg-muted',
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardDescription>{title}</CardDescription>
          <div className={`p-2 ${statusColors[status]}`}>{icon}</div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <CardTitle className="text-3xl">{value}</CardTitle>
        <div className="text-sm text-muted-foreground mt-1">{subtitle}</div>
      </CardContent>
    </Card>
  )
}

interface PlaceholderSectionProps {
  title: string
  description: string
}

function PlaceholderSection({ title, description }: PlaceholderSectionProps) {
  return (
    <Card className="border-dashed">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity className="size-4" />
          <span>Coming soon</span>
        </div>
      </CardContent>
    </Card>
  )
}

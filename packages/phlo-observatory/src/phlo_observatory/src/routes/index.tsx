import { createFileRoute } from '@tanstack/react-router'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  RefreshCw,
  Wifi,
  WifiOff,
  Wrench,
} from 'lucide-react'
import type {
  DagsterConnectionStatus,
  HealthMetrics,
} from '@/server/dagster.server'
import type { MaintenanceStatusSnapshot } from '@/server/maintenance.server'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { formatTimeSince, useRealtimePolling } from '@/hooks/useRealtimePolling'
import {
  checkDagsterConnection,
  getHealthMetrics,
} from '@/server/dagster.server'
import { getMaintenanceStatus as fetchMaintenanceStatus } from '@/server/maintenance.server'
import { formatDateTime } from '@/utils/dateFormat'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'

export const Route = createFileRoute('/')({
  loader: async () => {
    const settings = await getEffectiveObservatorySettings()
    const dagsterUrl = settings.connections.dagsterGraphqlUrl
    // Check connection and fetch metrics in parallel
    const [connection, metrics, maintenance] = await Promise.all([
      checkDagsterConnection({ data: { dagsterUrl } }),
      getHealthMetrics({ data: { dagsterUrl } }),
      fetchMaintenanceStatus({ data: {} }),
    ])
    return { connection, metrics, maintenance }
  },
  component: Dashboard,
})

function Dashboard() {
  const {
    connection: initialConnection,
    metrics: initialMetrics,
    maintenance: initialMaintenance,
  } = Route.useLoaderData()
  const { settings } = useObservatorySettings()

  // Real-time polling for health metrics
  const {
    data: metrics,
    isPolling,
    dataUpdatedAt,
    refetch,
  } = useRealtimePolling({
    queryKey: ['health-metrics', settings.connections.dagsterGraphqlUrl],
    queryFn: () =>
      getHealthMetrics({
        data: { dagsterUrl: settings.connections.dagsterGraphqlUrl },
      }),
    initialData: initialMetrics,
  })

  // Also poll connection status (less frequently is fine since it's cached)
  const { data: connection } = useRealtimePolling({
    queryKey: ['dagster-connection', settings.connections.dagsterGraphqlUrl],
    queryFn: () =>
      checkDagsterConnection({
        data: { dagsterUrl: settings.connections.dagsterGraphqlUrl },
      }),
    initialData: initialConnection,
  })

  const hasError = metrics && 'error' in metrics
  const healthData = hasError ? null : metrics
  const { data: maintenanceResponse } = useRealtimePolling({
    queryKey: ['maintenance-status'],
    queryFn: () => fetchMaintenanceStatus({ data: {} }),
    initialData: initialMaintenance,
  })
  const maintenanceData =
    maintenanceResponse && 'error' in maintenanceResponse
      ? null
      : maintenanceResponse

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
          <div className="flex items-center gap-2">
            {isPolling && (
              <span className="text-xs text-muted-foreground">
                Updated {formatTimeSince(dataUpdatedAt)}
              </span>
            )}
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Connection Status Banner */}
        {connection && <ConnectionBanner connection={connection} />}

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
          <HealthCard
            title="Maintenance"
            value={getMaintenanceValue(maintenanceData)}
            subtitle={getMaintenanceSubtitle(maintenanceData)}
            icon={<Wrench className="w-6 h-6" />}
            status={getMaintenanceHealthStatus(maintenanceData)}
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
            Last updated:{' '}
            {formatDateTime(
              new Date(healthData.lastUpdated),
              settings.ui.dateFormat,
            )}
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
  data: HealthMetrics | null | undefined,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.assetsTotal === 0) return 'warning'
  return 'success'
}

function getFailedJobsStatus(
  data: HealthMetrics | null | undefined,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.failedJobs24h === 0) return 'success'
  if (data.failedJobs24h <= 2) return 'warning'
  return 'error'
}

function getQualityStatus(
  data: HealthMetrics | null | undefined,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.qualityChecksTotal === 0) return 'loading' // Not implemented yet
  const ratio = data.qualityChecksPassing / data.qualityChecksTotal
  if (ratio === 1) return 'success'
  if (ratio >= 0.9) return 'warning'
  return 'error'
}

function getFreshnessStatus(
  data: HealthMetrics | null | undefined,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.assetsTotal === 0) return 'loading'
  const staleRatio = data.staleAssets / data.assetsTotal
  if (staleRatio === 0) return 'success'
  if (staleRatio <= 0.1) return 'warning'
  return 'error'
}

function getMaintenanceHealthStatus(
  data: MaintenanceStatusSnapshot | null | undefined,
): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (!data.operations.length) return 'loading'
  const hasFailures = data.operations.some((op) => op.status === 'failure')
  return hasFailures ? 'error' : 'success'
}

function getMaintenanceValue(
  data: MaintenanceStatusSnapshot | null | undefined,
): string {
  if (!data) return '--'
  if (!data.operations.length) return '--'
  const hasFailures = data.operations.some((op) => op.status === 'failure')
  return hasFailures ? 'Issues' : 'Healthy'
}

function getMaintenanceSubtitle(
  data: MaintenanceStatusSnapshot | null | undefined,
): string {
  if (!data) return 'No telemetry yet'
  if (!data.operations.length) return 'No maintenance runs'
  const latest = [...data.operations].sort(
    (a, b) =>
      new Date(b.completedAt).getTime() - new Date(a.completedAt).getTime(),
  )[0]
  return `Last run ${formatTimeSince(new Date(latest.completedAt).getTime())}`
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

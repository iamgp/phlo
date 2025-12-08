import { checkDagsterConnection, getHealthMetrics, type DagsterConnectionStatus, type HealthMetrics } from '@/server/dagster.server'
import { createFileRoute, useRouter } from '@tanstack/react-router'
import { Activity, AlertTriangle, CheckCircle, Clock, Database, RefreshCw, Wifi, WifiOff } from 'lucide-react'

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

  const isConnected = connection.connected
  const hasError = 'error' in metrics
  const healthData = hasError ? null : (metrics as HealthMetrics)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Platform Health</h1>
          <p className="text-slate-400">Overview of your data platform status</p>
        </div>
        <button
          onClick={() => router.invalidate()}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Connection Status Banner */}
      <ConnectionBanner connection={connection} />

      {/* Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <HealthCard
          title="Assets"
          value={healthData?.assetsTotal?.toString() ?? '--'}
          subtitle={healthData ? `${healthData.assetsHealthy} healthy` : 'Total registered'}
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
          value={healthData ? `${healthData.qualityChecksPassing}/${healthData.qualityChecksTotal}` : '--'}
          subtitle="Passing"
          icon={<CheckCircle className="w-6 h-6" />}
          status={getQualityStatus(healthData)}
        />
        <HealthCard
          title="Freshness"
          value={healthData ? `${healthData.assetsTotal - healthData.staleAssets}/${healthData.assetsTotal}` : '--'}
          subtitle="Assets up to date"
          icon={<Clock className="w-6 h-6" />}
          status={getFreshnessStatus(healthData)}
        />
      </div>

      {/* Placeholder Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
        <div className="mt-8 text-sm text-slate-500 text-right">
          Last updated: {new Date(healthData.lastUpdated).toLocaleString()}
        </div>
      )}
    </div>
  )
}

function ConnectionBanner({ connection }: { connection: DagsterConnectionStatus }) {
  if (connection.connected) {
    return (
      <div className="mb-6 p-4 bg-green-900/20 border border-green-700/50 rounded-xl flex items-center gap-3">
        <Wifi className="w-5 h-5 text-green-400" />
        <span className="text-green-300">
          Connected to Dagster{connection.version ? ` (v${connection.version})` : ''}
        </span>
      </div>
    )
  }

  return (
    <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-xl">
      <div className="flex items-center gap-3">
        <WifiOff className="w-5 h-5 text-yellow-400" />
        <span className="text-yellow-300">Cannot connect to Dagster</span>
      </div>
      {connection.error && (
        <p className="mt-2 text-sm text-yellow-400/70">{connection.error}</p>
      )}
      <p className="mt-2 text-sm text-slate-500">
        Make sure Dagster is running: <code className="px-2 py-0.5 bg-slate-800 rounded">docker compose up dagster-webserver</code>
      </p>
    </div>
  )
}

// Status helper functions
function getAssetStatus(data: HealthMetrics | null): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.assetsTotal === 0) return 'warning'
  return 'success'
}

function getFailedJobsStatus(data: HealthMetrics | null): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.failedJobs24h === 0) return 'success'
  if (data.failedJobs24h <= 2) return 'warning'
  return 'error'
}

function getQualityStatus(data: HealthMetrics | null): 'success' | 'warning' | 'error' | 'loading' {
  if (!data) return 'loading'
  if (data.qualityChecksTotal === 0) return 'loading' // Not implemented yet
  const ratio = data.qualityChecksPassing / data.qualityChecksTotal
  if (ratio === 1) return 'success'
  if (ratio >= 0.9) return 'warning'
  return 'error'
}

function getFreshnessStatus(data: HealthMetrics | null): 'success' | 'warning' | 'error' | 'loading' {
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
  icon: React.ReactNode
  status: 'success' | 'warning' | 'error' | 'loading'
}

function HealthCard({ title, value, subtitle, icon, status }: HealthCardProps) {
  const statusColors = {
    success: 'text-green-400 bg-green-400/10',
    warning: 'text-yellow-400 bg-yellow-400/10',
    error: 'text-red-400 bg-red-400/10',
    loading: 'text-slate-400 bg-slate-400/10',
  }

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <span className="text-slate-400 font-medium">{title}</span>
        <div className={`p-2 rounded-lg ${statusColors[status]}`}>{icon}</div>
      </div>
      <div className="text-3xl font-bold mb-1">{value}</div>
      <div className="text-sm text-slate-500">{subtitle}</div>
    </div>
  )
}

interface PlaceholderSectionProps {
  title: string
  description: string
}

function PlaceholderSection({ title, description }: PlaceholderSectionProps) {
  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 border-dashed">
      <h3 className="text-lg font-semibold mb-2 text-slate-300">{title}</h3>
      <p className="text-slate-500">{description}</p>
      <div className="mt-4 flex items-center gap-2 text-sm text-slate-600">
        <Activity className="w-4 h-4" />
        <span>Coming in Phase 1</span>
      </div>
    </div>
  )
}

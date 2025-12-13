import { Link, createFileRoute, useRouter } from '@tanstack/react-router'
import {
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Clock,
  RefreshCw,
  Shield,
  XCircle,
} from 'lucide-react'
import type { QualityCheck, QualityOverview } from '@/server/quality.server'
import { getQualityDashboard } from '@/server/quality.server'

export const Route = createFileRoute('/quality/')({
  loader: async () => {
    const result = await getQualityDashboard()
    return { data: result }
  },
  component: QualityDashboard,
})

function QualityDashboard() {
  const { data } = Route.useLoaderData()
  const router = useRouter()

  const hasError = 'error' in data
  const dashboardData = hasError
    ? null
    : (data as {
        overview: QualityOverview
        failingChecks: Array<QualityCheck>
      })

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Quality Center</h1>
          <p className="text-slate-400">
            Centralized data quality monitoring and management
          </p>
        </div>
        <button
          onClick={() => router.invalidate()}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {hasError ? (
        <div className="p-6 bg-yellow-900/20 border border-yellow-700/50 rounded-xl">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-300">Unable to load quality data</span>
          </div>
          <p className="mt-2 text-sm text-yellow-400/70">{data.error}</p>
        </div>
      ) : (
        <>
          {/* Quality Score */}
          <div className="mb-8">
            <QualityScoreCard
              score={dashboardData!.overview.qualityScore}
              totalChecks={dashboardData!.overview.totalChecks}
            />
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              title="Total Checks"
              value={dashboardData!.overview.totalChecks}
              icon={<Shield className="w-5 h-5 text-cyan-400" />}
            />
            <StatCard
              title="Passing"
              value={dashboardData!.overview.passingChecks}
              icon={<CheckCircle className="w-5 h-5 text-green-400" />}
              variant="success"
            />
            <StatCard
              title="Failing"
              value={dashboardData!.overview.failingChecks}
              icon={<XCircle className="w-5 h-5 text-red-400" />}
              variant={
                dashboardData!.overview.failingChecks > 0 ? 'error' : 'default'
              }
            />
            <StatCard
              title="Warnings"
              value={dashboardData!.overview.warningChecks}
              icon={<AlertTriangle className="w-5 h-5 text-yellow-400" />}
              variant={
                dashboardData!.overview.warningChecks > 0
                  ? 'warning'
                  : 'default'
              }
            />
          </div>

          {/* Categories and Failing Checks */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* By Category */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-cyan-400" />
                Quality by Category
              </h2>
              {dashboardData!.overview.byCategory.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData!.overview.byCategory.map((cat) => (
                    <CategoryBar key={cat.category} {...cat} />
                  ))}
                </div>
              ) : (
                <div className="text-center text-slate-500 py-8">
                  <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No quality categories defined</p>
                </div>
              )}
            </div>

            {/* Failing Checks */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-400" />
                Failing Checks
                {dashboardData!.failingChecks.length > 0 && (
                  <span className="ml-auto text-sm bg-red-600 text-white px-2 py-0.5 rounded">
                    {dashboardData!.failingChecks.length}
                  </span>
                )}
              </h2>
              {dashboardData!.failingChecks.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData!.failingChecks.map((check) => (
                    <FailingCheckCard key={check.name} check={check} />
                  ))}
                </div>
              ) : (
                <div className="text-center text-slate-500 py-8">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400 opacity-50" />
                  <p className="text-green-400">All checks passing!</p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="mt-6 bg-slate-800 rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-cyan-400" />
              Recent Check Executions
            </h2>
            <div className="text-center text-slate-500 py-8">
              <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Check execution history will appear here</p>
              <p className="text-sm mt-1">Run quality checks to see results</p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// Quality Score Card
interface QualityScoreCardProps {
  score: number
  totalChecks: number
}

function QualityScoreCard({ score, totalChecks }: QualityScoreCardProps) {
  const getScoreColor = (value: number) => {
    if (totalChecks === 0) return 'text-slate-400'
    if (value >= 90) return 'text-green-400'
    if (value >= 70) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreBg = (value: number) => {
    if (totalChecks === 0) return 'bg-slate-600'
    if (value >= 90) return 'bg-green-400'
    if (value >= 70) return 'bg-yellow-400'
    return 'bg-red-400'
  }

  return (
    <div className="bg-gradient-to-r from-slate-800 to-slate-800/50 rounded-xl border border-slate-700 p-6">
      <div className="flex items-center gap-8">
        <div className="flex-shrink-0">
          <div className="relative w-32 h-32">
            {/* Background circle */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                className="text-slate-700"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${(score / 100) * 352} 352`}
                strokeLinecap="round"
                className={getScoreBg(score)}
              />
            </svg>
            {/* Score text */}
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-3xl font-bold ${getScoreColor(score)}`}>
                {totalChecks === 0 ? '—' : `${score}%`}
              </span>
            </div>
          </div>
        </div>
        <div>
          <h3 className="text-xl font-semibold mb-1">Overall Quality Score</h3>
          {totalChecks === 0 ? (
            <>
              <p className="text-slate-400 mb-3">
                No quality checks configured yet
              </p>
              <p className="text-sm text-slate-500">
                Add{' '}
                <code className="bg-slate-700 px-1 rounded">@phlo.quality</code>{' '}
                decorators to your assets to enable quality monitoring
              </p>
            </>
          ) : (
            <p className="text-slate-400 mb-3">
              Based on {totalChecks} configured quality check
              {totalChecks !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// Stat Card
interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error'
}

function StatCard({ title, value, icon, variant = 'default' }: StatCardProps) {
  const variantStyles = {
    default: 'border-slate-700',
    success: 'border-green-700/50 bg-green-900/10',
    warning: 'border-yellow-700/50 bg-yellow-900/10',
    error: 'border-red-700/50 bg-red-900/10',
  }

  return (
    <div
      className={`bg-slate-800 rounded-xl border p-4 ${variantStyles[variant]}`}
    >
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-slate-400 text-sm">{title}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}

// Category Bar
interface CategoryBarProps {
  category: string
  passing: number
  total: number
  percentage: number
}

function CategoryBar({
  category,
  passing,
  total,
  percentage,
}: CategoryBarProps) {
  const getBarColor = (pct: number) => {
    if (pct >= 90) return 'bg-green-500'
    if (pct >= 70) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium">{category}</span>
        <span className="text-sm text-slate-400">
          {passing}/{total} ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${getBarColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Failing Check Card
interface FailingCheckCardProps {
  check: QualityCheck
}

function FailingCheckCard({ check }: FailingCheckCardProps) {
  const assetPath = check.assetKey.join('/')

  return (
    <Link
      to="/assets/$assetId"
      params={{ assetId: assetPath }}
      className="block p-3 bg-red-900/20 hover:bg-red-900/30 border border-red-700/50 rounded-lg transition-colors"
    >
      <div className="flex items-center gap-3">
        <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-red-300 truncate">{check.name}</div>
          <div className="text-xs text-slate-400 truncate">{assetPath}</div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
      </div>
      {check.lastExecutionTime && (
        <div className="mt-2 text-xs text-slate-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Failed {formatRelativeTime(new Date(check.lastExecutionTime))}
        </div>
      )}
    </Link>
  )
}

// Utility
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

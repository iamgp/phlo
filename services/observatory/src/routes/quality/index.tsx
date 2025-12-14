import { Link, createFileRoute, useRouter } from '@tanstack/react-router'
import {
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Clock,
  Copy,
  Filter,
  RefreshCw,
  Search,
  Shield,
  XCircle,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type {
  QualityCheck,
  QualityOverview,
  RecentCheckExecution,
} from '@/server/quality.server'
import { getCheckHistory, getQualityDashboard } from '@/server/quality.server'

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
        recentExecutions: Array<RecentCheckExecution>
        checks: Array<QualityCheck>
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
            {dashboardData!.recentExecutions.length > 0 ? (
              <div className="space-y-2">
                {dashboardData!.recentExecutions.map((exec) => (
                  <RecentExecutionRow
                    key={`${exec.assetKey.join('/')}::${exec.checkName}::${exec.timestamp}`}
                    exec={exec}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center text-slate-500 py-8">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No check executions yet</p>
                <p className="text-sm mt-1">
                  Run a materialization or check to see results
                </p>
              </div>
            )}
          </div>

          {/* All Checks */}
          <div className="mt-6 bg-slate-800 rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-cyan-400" />
              All Checks
              <span className="ml-auto text-sm text-slate-400">
                {dashboardData!.checks.length}
              </span>
            </h2>
            <ChecksTable checks={dashboardData!.checks} />
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

function RecentExecutionRow({ exec }: { exec: RecentCheckExecution }) {
  const statusColor =
    exec.status === 'PASSED'
      ? 'text-green-400'
      : exec.severity === 'WARN'
        ? 'text-yellow-400'
        : 'text-red-400'

  const icon =
    exec.status === 'PASSED' ? (
      <CheckCircle className="w-4 h-4 text-green-400" />
    ) : exec.severity === 'WARN' ? (
      <AlertTriangle className="w-4 h-4 text-yellow-400" />
    ) : (
      <XCircle className="w-4 h-4 text-red-400" />
    )

  const assetId = exec.assetKey.join('/')
  const assetLabel = exec.assetKey[exec.assetKey.length - 1] || assetId

  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-700/40 transition-colors">
      {icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Link
            to="/assets/$assetId"
            params={{ assetId }}
            className="text-sm font-medium text-slate-200 hover:text-cyan-300 transition-colors truncate"
          >
            {assetLabel}
          </Link>
          <ChevronRight className="w-3 h-3 text-slate-500 flex-shrink-0" />
          <span className="text-sm text-slate-300 truncate">
            {exec.checkName}
          </span>
        </div>
        <div className="text-xs text-slate-500">
          {new Date(exec.timestamp).toLocaleString()}
        </div>
      </div>
      <span className={`text-xs font-semibold ${statusColor}`}>
        {exec.status}
      </span>
    </div>
  )
}

type CheckKind = 'all' | 'pandera' | 'dbt' | 'custom'
type CheckStatusFilter = 'all' | 'PASSED' | 'FAILED' | 'WARN'
type LayerFilter = 'all' | 'bronze' | 'silver' | 'gold' | 'marts'

function ChecksTable({ checks }: { checks: Array<QualityCheck> }) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<CheckStatusFilter>('all')
  const [kind, setKind] = useState<CheckKind>('all')
  const [layer, setLayer] = useState<LayerFilter>('all')
  const [selected, setSelected] = useState<QualityCheck | null>(null)

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    return checks
      .filter((check) => {
        if (!query) return true
        const asset = check.assetKey.join('/').toLowerCase()
        return check.name.toLowerCase().includes(query) || asset.includes(query)
      })
      .filter((check) => {
        if (kind === 'all') return true
        if (kind === 'pandera') return check.name === 'pandera_contract'
        if (kind === 'dbt') return check.name.startsWith('dbt__')
        return (
          check.name !== 'pandera_contract' && !check.name.startsWith('dbt__')
        )
      })
      .filter((check) => {
        if (status === 'all') return true
        if (status === 'WARN')
          return check.status === 'FAILED' && check.severity === 'WARN'
        return check.status === status
      })
      .filter((check) => {
        if (layer === 'all') return true
        const asset = check.assetKey[check.assetKey.length - 1] || ''
        const inferred = asset.startsWith('dlt_')
          ? 'bronze'
          : inferSchemaFromAssetName(asset)
        return inferred === layer
      })
      .sort((a, b) => {
        const aKey = a.assetKey.join('/')
        const bKey = b.assetKey.join('/')
        if (aKey !== bKey) return aKey < bKey ? -1 : 1
        return a.name < b.name ? -1 : 1
      })
  }, [checks, kind, layer, search, status])

  return (
    <>
      <div className="flex flex-col md:flex-row md:items-center gap-3 mb-4">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by asset or check name"
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as CheckKind)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm"
          >
            <option value="all">All</option>
            <option value="pandera">Pandera</option>
            <option value="dbt">dbt</option>
            <option value="custom">Custom</option>
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as CheckStatusFilter)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm"
          >
            <option value="all">All statuses</option>
            <option value="PASSED">Passed</option>
            <option value="FAILED">Failed</option>
            <option value="WARN">Warn</option>
          </select>
          <select
            value={layer}
            onChange={(e) => setLayer(e.target.value as LayerFilter)}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm"
          >
            <option value="all">All layers</option>
            <option value="bronze">Bronze</option>
            <option value="silver">Silver</option>
            <option value="gold">Gold</option>
            <option value="marts">Marts</option>
          </select>
        </div>
      </div>

      {filtered.length > 0 ? (
        <div className="overflow-x-auto border border-slate-700 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/60">
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 px-3 font-medium text-slate-400">
                  Status
                </th>
                <th className="text-left py-2 px-3 font-medium text-slate-400">
                  Asset
                </th>
                <th className="text-left py-2 px-3 font-medium text-slate-400">
                  Check
                </th>
                <th className="text-left py-2 px-3 font-medium text-slate-400">
                  Partition
                </th>
                <th className="text-left py-2 px-3 font-medium text-slate-400">
                  Last run
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((check) => (
                <tr
                  key={`${check.assetKey.join('/')}::${check.name}`}
                  className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer"
                  onClick={() => setSelected(check)}
                >
                  <td className="py-2 px-3">
                    <StatusPill
                      status={check.status}
                      severity={check.severity}
                    />
                  </td>
                  <td className="py-2 px-3 font-mono text-xs text-cyan-300">
                    {check.assetKey.join('/')}
                  </td>
                  <td className="py-2 px-3 text-slate-200">{check.name}</td>
                  <td className="py-2 px-3 font-mono text-xs text-slate-400">
                    {String(check.lastResult?.metadata?.partition_key ?? '—')}
                  </td>
                  <td className="py-2 px-3 text-xs text-slate-400">
                    {check.lastExecutionTime
                      ? new Date(check.lastExecutionTime).toLocaleString()
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center text-slate-500 py-10">
          <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No checks match your filters</p>
        </div>
      )}

      {selected && (
        <CheckDetailsDrawer
          check={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  )
}

function StatusPill({
  status,
  severity,
}: {
  status: QualityCheck['status']
  severity: QualityCheck['severity']
}) {
  const isWarn = status === 'FAILED' && severity === 'WARN'
  const label = isWarn ? 'WARN' : status
  const className =
    status === 'PASSED'
      ? 'bg-green-600/20 text-green-300 border-green-700/40'
      : isWarn
        ? 'bg-yellow-600/20 text-yellow-300 border-yellow-700/40'
        : status === 'FAILED'
          ? 'bg-red-600/20 text-red-300 border-red-700/40'
          : 'bg-slate-600/20 text-slate-300 border-slate-700/40'

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 border rounded text-xs ${className}`}
    >
      {label}
    </span>
  )
}

function CheckDetailsDrawer({
  check,
  onClose,
}: {
  check: QualityCheck
  onClose: () => void
}) {
  const [history, setHistory] = useState<
    Array<{ timestamp: string; passed: boolean; runId?: string }>
  >([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const assetKeyPath = check.assetKey.join('/')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    void getCheckHistory({
      data: { assetKey: check.assetKey, checkName: check.name, limit: 20 },
    })
      .then((result) => {
        if (cancelled) return
        if ('error' in result) {
          setError(result.error)
          setHistory([])
          return
        }
        setHistory(result)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load history')
      })
      .finally(() => {
        if (cancelled) return
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [assetKeyPath, check.name])

  const metadata = check.lastResult?.metadata ?? {}
  const sql =
    (metadata.repro_sql as string | undefined) ||
    (metadata.query_or_sql as string | undefined)

  const openInSqlLink =
    sql && sql.length <= 1500 ? buildOpenInSqlLink(check.assetKey, sql) : null

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative ml-auto w-full max-w-xl h-full bg-slate-900 border-l border-slate-700 p-6 overflow-y-auto">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <div className="text-xs text-slate-500 font-mono">
              {check.assetKey.join('/')}
            </div>
            <h3 className="text-lg font-semibold text-slate-100">
              {check.name}
            </h3>
            <div className="mt-2">
              <StatusPill status={check.status} severity={check.severity} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 px-2 py-1 rounded hover:bg-slate-800"
          >
            Close
          </button>
        </div>

        {sql && (
          <Section title="SQL">
            <div className="flex items-center gap-2 mb-2">
              {openInSqlLink && (
                <Link
                  to={openInSqlLink.to}
                  params={openInSqlLink.params}
                  search={openInSqlLink.search}
                  className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm"
                >
                  Open in SQL
                  <ChevronRight className="w-4 h-4" />
                </Link>
              )}
              <button
                type="button"
                onClick={() => void navigator.clipboard.writeText(sql)}
                className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm"
              >
                <Copy className="w-4 h-4" />
                Copy
              </button>
              {sql.length > 1500 && (
                <span className="text-xs text-slate-500">
                  (Too large to embed in URL)
                </span>
              )}
            </div>
            <pre className="text-xs text-slate-200 whitespace-pre-wrap break-words bg-slate-800/60 border border-slate-700 rounded-lg p-3 max-h-64 overflow-auto">
              {sql}
            </pre>
          </Section>
        )}

        <Section title="Metadata">
          {Object.keys(metadata).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(metadata).map(([key, value]) => (
                <div
                  key={key}
                  className="bg-slate-800/60 border border-slate-700 rounded-lg p-3"
                >
                  <div className="text-xs text-slate-400 font-mono mb-1">
                    {key}
                  </div>
                  <pre className="text-xs text-slate-200 whitespace-pre-wrap break-words">
                    {formatMetadataValue(value)}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">No metadata.</div>
          )}
        </Section>

        <Section title="History">
          {loading ? (
            <div className="text-sm text-slate-500">Loading…</div>
          ) : error ? (
            <div className="text-sm text-red-400">{error}</div>
          ) : history.length > 0 ? (
            <div className="space-y-2">
              {history.map((item) => (
                <div
                  key={`${item.runId ?? 'run'}::${item.timestamp}`}
                  className="flex items-center justify-between bg-slate-800/60 border border-slate-700 rounded-lg p-3"
                >
                  <div className="text-sm text-slate-200">
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 font-mono">
                      {item.runId ?? '—'}
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        item.passed ? 'text-green-300' : 'text-red-300'
                      }`}
                    >
                      {item.passed ? 'PASSED' : 'FAILED'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">No history found.</div>
          )}
        </Section>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mb-6">
      <h4 className="text-sm font-semibold text-slate-200 mb-2">{title}</h4>
      {children}
    </div>
  )
}

function formatMetadataValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function buildOpenInSqlLink(
  assetKey: Array<string>,
  sql: string,
): {
  to: '/data/$schema/$table'
  params: { schema: string; table: string }
  search: { sql: string; tab: 'query' }
} | null {
  if (!assetKey.length) return null
  const name = assetKey[assetKey.length - 1] || ''
  if (!name) return null

  if (name.startsWith('dlt_')) {
    return {
      to: '/data/$schema/$table',
      params: { schema: 'bronze', table: name.slice(4) },
      search: { sql, tab: 'query' },
    }
  }

  const schema = inferSchemaFromAssetName(name)
  return {
    to: '/data/$schema/$table',
    params: { schema, table: name },
    search: { sql, tab: 'query' },
  }
}

function inferSchemaFromAssetName(name: string): string {
  if (name.startsWith('stg_')) return 'silver'
  if (name.startsWith('dim_') || name.startsWith('fct_')) return 'gold'
  if (name.startsWith('mrt_')) return 'marts'
  return 'bronze'
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

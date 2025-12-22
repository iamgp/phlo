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
import { Badge } from '@/components/ui/badge'
import { Button, buttonVariants } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'
import { getCheckHistory, getQualityDashboard } from '@/server/quality.server'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { formatDate, formatDateTime } from '@/utils/dateFormat'

export const Route = createFileRoute('/quality/')({
  loader: async () => {
    const settings = await getEffectiveObservatorySettings()
    const result = await getQualityDashboard({
      data: { dagsterUrl: settings.connections.dagsterGraphqlUrl },
    })
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
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold">Quality Center</h1>
            <p className="text-muted-foreground">
              Centralized data quality monitoring and management
            </p>
          </div>
          <Button variant="outline" onClick={() => router.invalidate()}>
            <RefreshCw className="size-4" />
            Refresh
          </Button>
        </div>

        {hasError ? (
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <span className="text-yellow-300">
                  Unable to load quality data
                </span>
              </div>
              <p className="mt-2 text-sm text-yellow-400/80">{data.error}</p>
            </CardContent>
          </Card>
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
                icon={<Shield className="w-5 h-5 text-primary" />}
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
                  dashboardData!.overview.failingChecks > 0
                    ? 'error'
                    : 'default'
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
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Shield className="w-5 h-5 text-primary" />
                    Quality by Category
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {dashboardData!.overview.byCategory.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData!.overview.byCategory.map((cat) => (
                        <CategoryBar key={cat.category} {...cat} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No quality categories defined</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Failing Checks */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <XCircle className="w-5 h-5 text-destructive" />
                    Failing Checks
                    {dashboardData!.failingChecks.length > 0 && (
                      <Badge variant="destructive" className="ml-auto">
                        {dashboardData!.failingChecks.length}
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {dashboardData!.failingChecks.length > 0 ? (
                    <div className="space-y-3">
                      {dashboardData!.failingChecks.map((check) => (
                        <FailingCheckCard key={check.name} check={check} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground py-8">
                      <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400 opacity-50" />
                      <p className="text-green-400">All checks passing!</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  Recent Check Executions
                </CardTitle>
              </CardHeader>
              <CardContent>
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
                  <div className="text-center text-muted-foreground py-8">
                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No check executions yet</p>
                    <p className="text-sm mt-1">
                      Run a materialization or check to see results
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* All Checks */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="w-5 h-5 text-primary" />
                  All Checks
                  <span className="ml-auto text-sm text-muted-foreground">
                    {dashboardData!.checks.length}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ChecksTable checks={dashboardData!.checks} />
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}

// Quality Score Card
interface QualityScoreCardProps {
  score: number
  totalChecks: number
}

function QualityScoreCard({ score, totalChecks }: QualityScoreCardProps) {
  const scoreLabel = totalChecks === 0 ? '—' : `${score}%`
  const scoreTone =
    totalChecks === 0
      ? 'text-muted-foreground'
      : score >= 90
        ? 'text-green-400'
        : score >= 70
          ? 'text-yellow-400'
          : 'text-red-400'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Overall Quality Score</CardTitle>
        <CardDescription>
          {totalChecks === 0
            ? 'No quality checks configured yet.'
            : `Based on ${totalChecks} configured quality check${totalChecks !== 1 ? 's' : ''}.`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline justify-between gap-4">
          <div className={cn('text-3xl font-bold', scoreTone)}>
            {scoreLabel}
          </div>
          {totalChecks === 0 && (
            <div className="text-sm text-muted-foreground">
              Add{' '}
              <code className="bg-muted px-1 rounded-none">@phlo.quality</code>{' '}
              to enable checks
            </div>
          )}
        </div>
        <div className="h-2 bg-muted overflow-hidden">
          <div
            className={cn(
              'h-full',
              totalChecks === 0 ? 'bg-muted-foreground/40' : 'bg-primary',
            )}
            style={{
              width: `${totalChecks === 0 ? 0 : Math.max(0, Math.min(100, score))}%`,
            }}
          />
        </div>
      </CardContent>
    </Card>
  )
}

function RecentExecutionRow({ exec }: { exec: RecentCheckExecution }) {
  const { settings } = useObservatorySettings()
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
    <div className="flex items-center gap-3 px-3 py-2 hover:bg-muted/50 transition-colors">
      {icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Link
            to="/assets/$assetId"
            params={{ assetId }}
            className="text-sm font-medium hover:underline transition-colors truncate"
          >
            {assetLabel}
          </Link>
          <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />
          <span className="text-sm text-muted-foreground truncate">
            {exec.checkName}
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          {formatDateTime(new Date(exec.timestamp), settings.ui.dateFormat)}
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
  const { settings } = useObservatorySettings()
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
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by asset or check name"
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as CheckKind)}
            className="h-8 px-3 bg-input/30 border border-input text-xs outline-none"
          >
            <option value="all">All</option>
            <option value="pandera">Pandera</option>
            <option value="dbt">dbt</option>
            <option value="custom">Custom</option>
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as CheckStatusFilter)}
            className="h-8 px-3 bg-input/30 border border-input text-xs outline-none"
          >
            <option value="all">All statuses</option>
            <option value="PASSED">Passed</option>
            <option value="FAILED">Failed</option>
            <option value="WARN">Warn</option>
          </select>
          <select
            value={layer}
            onChange={(e) => setLayer(e.target.value as LayerFilter)}
            className="h-8 px-3 bg-input/30 border border-input text-xs outline-none"
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
        <div className="overflow-x-auto border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Asset</TableHead>
                <TableHead>Check</TableHead>
                <TableHead>Partition</TableHead>
                <TableHead>Last run</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((check) => (
                <TableRow
                  key={`${check.assetKey.join('/')}::${check.name}`}
                  className="cursor-pointer"
                  onClick={() => setSelected(check)}
                >
                  <TableCell>
                    <StatusPill
                      status={check.status}
                      severity={check.severity}
                    />
                  </TableCell>
                  <TableCell className="font-mono text-xs text-primary">
                    {check.assetKey.join('/')}
                  </TableCell>
                  <TableCell>{check.name}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {String(check.lastResult?.metadata?.partition_key ?? '—')}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {check.lastExecutionTime
                      ? formatDateTime(
                          new Date(check.lastExecutionTime),
                          settings.ui.dateFormat,
                        )
                      : '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="text-center text-muted-foreground py-10">
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
      ? 'bg-green-500/10 text-green-400 border-green-500/30'
      : isWarn
        ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
        : 'bg-destructive/10 text-destructive border-destructive/30'

  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  )
}

function CheckDetailsDrawer({
  check,
  onClose,
}: {
  check: QualityCheck
  onClose: () => void
}) {
  const { settings } = useObservatorySettings()
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
      data: {
        assetKey: check.assetKey,
        checkName: check.name,
        limit: 20,
        dagsterUrl: settings.connections.dagsterGraphqlUrl,
      },
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
  }, [assetKeyPath, check.name, settings.connections.dagsterGraphqlUrl])

  const metadata = check.lastResult?.metadata ?? {}
  const sql =
    (metadata.repro_sql as string | undefined) ||
    (metadata.query_or_sql as string | undefined)

  const openInSqlLink =
    sql && sql.length <= 1500 ? buildOpenInSqlLink(check.assetKey, sql) : null

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative ml-auto w-full max-w-xl h-full bg-card border-l border-border p-6 overflow-y-auto">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <div className="text-xs text-muted-foreground font-mono">
              {check.assetKey.join('/')}
            </div>
            <h3 className="text-lg font-semibold">{check.name}</h3>
            <div className="mt-2">
              <StatusPill status={check.status} severity={check.severity} />
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        {sql && (
          <Section title="SQL">
            <div className="flex items-center gap-2 mb-2">
              {openInSqlLink && (
                <Link
                  to={openInSqlLink.to}
                  params={openInSqlLink.params}
                  search={openInSqlLink.search}
                  className={cn(
                    buttonVariants({ variant: 'outline', size: 'sm' }),
                    'gap-2',
                  )}
                >
                  Open in SQL
                  <ChevronRight className="w-4 h-4" />
                </Link>
              )}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void navigator.clipboard.writeText(sql)}
              >
                <Copy className="w-4 h-4" />
                Copy
              </Button>
              {sql.length > 1500 && (
                <span className="text-xs text-muted-foreground">
                  (Too large to embed in URL)
                </span>
              )}
            </div>
            <pre className="text-xs whitespace-pre-wrap break-words bg-muted border border-border p-3 max-h-64 overflow-auto">
              {sql}
            </pre>
          </Section>
        )}

        <Section title="Metadata">
          {Object.keys(metadata).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(metadata).map(([key, value]) => (
                <div key={key} className="bg-muted border border-border p-3">
                  <div className="text-xs text-muted-foreground font-mono mb-1">
                    {key}
                  </div>
                  <pre className="text-xs whitespace-pre-wrap break-words">
                    {formatMetadataValue(value)}
                  </pre>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground">No metadata.</div>
          )}
        </Section>

        <Section title="History">
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading…</div>
          ) : error ? (
            <div className="text-sm text-red-400">{error}</div>
          ) : history.length > 0 ? (
            <div className="space-y-2">
              {history.map((item) => (
                <div
                  key={`${item.runId ?? 'run'}::${item.timestamp}`}
                  className="flex items-center justify-between bg-muted border border-border p-3"
                >
                  <div className="text-sm">
                    {formatDateTime(
                      new Date(item.timestamp),
                      settings.ui.dateFormat,
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground font-mono">
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
            <div className="text-sm text-muted-foreground">
              No history found.
            </div>
          )}
        </Section>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mb-6">
      <h4 className="text-sm font-semibold mb-2">{title}</h4>
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
    default: 'border-border',
    success: 'border-green-500/30 bg-green-500/5',
    warning: 'border-yellow-500/30 bg-yellow-500/5',
    error: 'border-destructive/30 bg-destructive/5',
  }

  return (
    <Card className={variantStyles[variant]}>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-2">
            {icon}
            {title}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardContent>
    </Card>
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
        <span className="text-sm text-muted-foreground">
          {passing}/{total} ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 bg-muted overflow-hidden">
        <div
          className={`h-full transition-all ${getBarColor(percentage)}`}
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
  const { settings } = useObservatorySettings()

  return (
    <Link
      to="/assets/$assetId"
      params={{ assetId: assetPath }}
      className="block p-3 bg-destructive/10 hover:bg-destructive/15 border border-destructive/30 transition-colors"
    >
      <div className="flex items-center gap-3">
        <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-red-300 truncate">{check.name}</div>
          <div className="text-xs text-muted-foreground truncate">
            {assetPath}
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
      </div>
      {check.lastExecutionTime && (
        <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Failed{' '}
          {formatRelativeTime(
            new Date(check.lastExecutionTime),
            settings.ui.dateFormat,
          )}
        </div>
      )}
    </Link>
  )
}

// Utility
function formatRelativeTime(date: Date, mode: 'iso' | 'local'): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(date, mode)
}

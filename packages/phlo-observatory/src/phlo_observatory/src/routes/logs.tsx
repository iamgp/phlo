/**
 * Observability Page
 *
 * Shows services and their logs. Similar to Docker Desktop's view.
 * Supports filtering by runId, service, level, etc.
 */

import { createFileRoute, useSearch } from '@tanstack/react-router'
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Circle,
  ExternalLink,
  Filter,
  Info,
  Loader2,
  RefreshCw,
  Terminal,
  XCircle,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import type { LogEntry, LogQueryResult } from '@/server/loki.server'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { cn } from '@/lib/utils'
import { checkLokiConnection, queryLogs } from '@/server/loki.server'
import { formatDate } from '@/utils/dateFormat'

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface ServiceInfo {
  name: string
  displayName: string
  container: string
  port?: number
  status: 'running' | 'stopped' | 'unknown'
}

const SERVICES: Array<ServiceInfo> = [
  {
    name: 'dagster',
    displayName: 'Dagster',
    container: 'dagster',
    port: 3000,
    status: 'unknown',
  },
  {
    name: 'observatory',
    displayName: 'Observatory',
    container: 'observatory',
    port: 3001,
    status: 'unknown',
  },
  {
    name: 'trino',
    displayName: 'Trino',
    container: 'trino',
    port: 8080,
    status: 'unknown',
  },
  {
    name: 'nessie',
    displayName: 'Nessie',
    container: 'nessie',
    port: 19120,
    status: 'unknown',
  },
  {
    name: 'postgres',
    displayName: 'Postgres',
    container: 'postgres',
    port: 5432,
    status: 'unknown',
  },
  {
    name: 'minio',
    displayName: 'MinIO',
    container: 'minio',
    port: 9000,
    status: 'unknown',
  },
  {
    name: 'loki',
    displayName: 'Loki',
    container: 'loki',
    port: 3100,
    status: 'unknown',
  },
  {
    name: 'grafana',
    displayName: 'Grafana',
    container: 'grafana',
    port: 3002,
    status: 'unknown',
  },
]

const levelColors: Record<string, string> = {
  debug: 'text-muted-foreground',
  info: 'text-blue-400',
  warn: 'text-yellow-400',
  error: 'text-red-400',
}

const levelIcons: Record<string, React.ReactNode> = {
  debug: <Terminal className="w-3 h-3" />,
  info: <Info className="w-3 h-3" />,
  warn: <AlertTriangle className="w-3 h-3" />,
  error: <AlertCircle className="w-3 h-3" />,
}

export const Route = createFileRoute('/logs')({
  validateSearch: (
    search: Record<string, unknown>,
  ): {
    runId?: string
    service?: string
    level?: LogLevel
  } => ({
    runId: (search.runId as string) || undefined,
    service: (search.service as string) || undefined,
    level: (search.level as LogLevel) || undefined,
  }),
  component: ObservabilityPage,
})

function ObservabilityPage() {
  const search = useSearch({ from: '/logs' })
  const { settings } = useObservatorySettings()

  const [selectedService, setSelectedService] = useState<string | null>(
    search.service || null,
  )
  const [logs, setLogs] = useState<Array<LogEntry>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<LogLevel | 'all'>(
    search.level || 'all',
  )
  const [hoursBack, setHoursBack] = useState(24)
  const [lokiConnected, setLokiConnected] = useState<boolean | null>(null)

  const grafanaUrl = 'http://localhost:3002'

  // Check Loki connection
  useEffect(() => {
    async function checkConnection() {
      const result = await checkLokiConnection({ data: {} })
      setLokiConnected(result.connected)
    }
    void checkConnection()
  }, [])

  const loadLogs = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const end = new Date()
      const start = new Date(end.getTime() - hoursBack * 60 * 60 * 1000)

      const result: LogQueryResult | { error: string } = await queryLogs({
        data: {
          runId: search.runId,
          service: selectedService || undefined,
          level: levelFilter === 'all' ? undefined : levelFilter,
          start: start.toISOString(),
          end: end.toISOString(),
          limit: 500,
        },
      })

      if ('error' in result) {
        setError(result.error)
      } else {
        setLogs(result.entries)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs')
    } finally {
      setLoading(false)
    }
  }, [search.runId, selectedService, levelFilter, hoursBack])

  useEffect(() => {
    void loadLogs()
  }, [loadLogs])

  // Build Grafana explore URL
  const buildGrafanaUrl = () => {
    let query = '{}'
    if (selectedService) {
      query = `{container="${selectedService}"}`
    }
    if (search.runId) {
      query += ` | json | run_id="${search.runId}"`
    }
    const encoded = encodeURIComponent(query)
    return `${grafanaUrl}/explore?orgId=1&left=["now-${hoursBack}h","now","Loki",{"expr":"${encoded}"}]`
  }

  return (
    <div className="flex h-full">
      {/* Services sidebar */}
      <aside className="w-56 border-r bg-sidebar text-sidebar-foreground flex flex-col">
        <div className="px-4 py-3 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-sidebar-primary" />
            Services
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            {lokiConnected === true && (
              <span className="text-green-400">Loki connected</span>
            )}
            {lokiConnected === false && (
              <span className="text-red-400">Loki not connected</span>
            )}
            {lokiConnected === null && (
              <span className="text-muted-foreground">Checking...</span>
            )}
          </p>
        </div>

        <div className="flex-1 overflow-auto py-2">
          {/* All services option */}
          <button
            onClick={() => setSelectedService(null)}
            className={cn(
              'w-full px-4 py-2 text-left flex items-center gap-3 hover:bg-sidebar-accent/50',
              selectedService === null && 'bg-sidebar-accent',
            )}
          >
            <Circle className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">All Services</span>
          </button>

          {SERVICES.map((service) => (
            <button
              key={service.name}
              onClick={() => setSelectedService(service.name)}
              className={cn(
                'w-full px-4 py-2 text-left flex items-center gap-3 hover:bg-sidebar-accent/50',
                selectedService === service.name && 'bg-sidebar-accent',
              )}
            >
              <div className="relative">
                <Circle className="w-4 h-4 text-muted-foreground" />
                {/* Status dot */}
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{service.displayName}</div>
                {service.port && (
                  <div className="text-xs text-muted-foreground">
                    :{service.port}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* Main logs area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="px-4 py-3 border-b bg-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold flex items-center gap-2">
              <Terminal className="w-5 h-5 text-primary" />
              Logs
            </h1>
            {search.runId && (
              <Badge variant="secondary" className="font-mono">
                Run: {search.runId.slice(0, 8)}...
              </Badge>
            )}
            {logs.length > 0 && (
              <Badge variant="outline">{logs.length} entries</Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Time range */}
            <Select
              value={String(hoursBack)}
              onValueChange={(v) => v && setHoursBack(Number(v))}
            >
              <SelectTrigger className="w-24 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 hour</SelectItem>
                <SelectItem value="6">6 hours</SelectItem>
                <SelectItem value="24">24 hours</SelectItem>
                <SelectItem value="72">3 days</SelectItem>
                <SelectItem value="168">7 days</SelectItem>
              </SelectContent>
            </Select>

            {/* Level filter */}
            <Select
              value={levelFilter}
              onValueChange={(v) => v && setLevelFilter(v as LogLevel | 'all')}
            >
              <SelectTrigger className="w-24 h-8 text-xs">
                <Filter className="w-3 h-3 mr-1" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="debug">Debug</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="warn">Warn</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>

            {/* Refresh */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => void loadLogs()}
              disabled={loading}
            >
              <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            </Button>

            {/* Grafana link */}
            <a
              href={buildGrafanaUrl()}
              target="_blank"
              rel="noopener noreferrer"
              title="Open in Grafana"
              className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent hover:text-accent-foreground"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </header>

        {/* Log content */}
        <div className="flex-1 overflow-auto bg-black/20 font-mono text-xs p-2">
          {loading && logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Loading logs...
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full text-red-400">
              <XCircle className="w-8 h-8 mb-2" />
              <p>{error}</p>
              {!lokiConnected && (
                <p className="text-sm mt-2 text-muted-foreground">
                  Start Loki:{' '}
                  <code className="bg-muted px-1">
                    phlo services start --profile observability
                  </code>
                </p>
              )}
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Terminal className="w-8 h-8 mb-2 opacity-50" />
              <p>No logs found</p>
              <p className="text-xs mt-1">
                {search.runId
                  ? `No logs for run ${search.runId.slice(0, 8)}...`
                  : `No logs in the last ${hoursBack} hours`}
              </p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {logs.map((log, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'flex items-start gap-2 py-0.5 px-1 hover:bg-white/5 rounded',
                    levelColors[log.level] || 'text-foreground',
                  )}
                >
                  {/* Level icon */}
                  <span className="flex-shrink-0 mt-0.5">
                    {levelIcons[log.level] || levelIcons.info}
                  </span>

                  {/* Timestamp */}
                  <span className="flex-shrink-0 text-muted-foreground w-44">
                    {formatDate(
                      log.timestamp,
                      settings?.ui?.dateFormat || 'relative',
                    )}
                  </span>

                  {/* Service badge */}
                  {log.metadata.fn && (
                    <Badge
                      variant="outline"
                      className="text-[10px] px-1 py-0 h-4 flex-shrink-0"
                    >
                      {log.metadata.fn}
                    </Badge>
                  )}

                  {/* Message */}
                  <span className="flex-1 break-all whitespace-pre-wrap">
                    {log.message}
                  </span>

                  {/* Duration */}
                  {log.metadata.durationMs && (
                    <span className="text-muted-foreground flex-shrink-0">
                      {log.metadata.durationMs}ms
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

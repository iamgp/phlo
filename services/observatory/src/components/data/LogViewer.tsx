/**
 * Log Viewer Component
 *
 * Displays logs from Loki filtered by asset, run, or quality check.
 * Supports level filtering and links to Grafana for advanced queries.
 */

import { useCallback, useEffect, useState } from 'react'

import {
  AlertCircle,
  AlertTriangle,
  ExternalLink,
  Filter,
  Info,
  Loader2,
  RefreshCw,
  Terminal,
} from 'lucide-react'

import type { LogEntry, LogQueryResult } from '@/server/loki.server'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { cn } from '@/lib/utils'
import { queryAssetLogs, queryRunLogs } from '@/server/loki.server'
import { formatDate } from '@/utils/dateFormat'

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'all'

interface LogViewerProps {
  assetKey?: string
  runId?: string
  partitionKey?: string
  className?: string
}

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

export function LogViewer({
  assetKey,
  runId,
  partitionKey,
  className,
}: LogViewerProps) {
  const { settings } = useObservatorySettings()
  const [logs, setLogs] = useState<Array<LogEntry>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<LogLevel>('all')
  const [hoursBack, setHoursBack] = useState(24)

  const grafanaUrl = 'http://localhost:3000'

  const loadLogs = useCallback(async () => {
    if (!assetKey && !runId) return

    setLoading(true)
    setError(null)

    try {
      let result: LogQueryResult | { error: string }

      if (runId) {
        result = await queryRunLogs({
          data: {
            runId,
            level: levelFilter === 'all' ? undefined : levelFilter,
            limit: 200,
          },
        })
      } else if (assetKey) {
        result = await queryAssetLogs({
          data: {
            assetKey,
            partitionKey,
            level: levelFilter === 'all' ? undefined : levelFilter,
            hoursBack,
            limit: 200,
          },
        })
      } else {
        return
      }

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
  }, [assetKey, runId, partitionKey, levelFilter, hoursBack])

  useEffect(() => {
    void loadLogs()
  }, [loadLogs])

  // Build Grafana explore URL
  const buildGrafanaUrl = () => {
    const query = assetKey
      ? `{} | json | asset_key="${assetKey}"`
      : `{} | json | run_id="${runId}"`
    const encoded = encodeURIComponent(query)
    return `${grafanaUrl}/explore?orgId=1&left=["now-${hoursBack}h","now","Loki",{"expr":"${encoded}"}]`
  }

  // Filter logs by level for display
  const filteredLogs =
    levelFilter === 'all'
      ? logs
      : logs.filter((log) => log.level === levelFilter)

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Terminal className="w-4 h-4 text-primary" />
            Logs
            {filteredLogs.length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {filteredLogs.length}
              </Badge>
            )}
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Time range select */}
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
              onValueChange={(v) => v && setLevelFilter(v as LogLevel)}
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

            {/* Refresh button */}
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
        </div>
      </CardHeader>

      <CardContent>
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Loading logs...
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-8 text-red-400">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Terminal className="w-8 h-8 mb-2 opacity-50" />
            <p>No logs found</p>
            <p className="text-sm mt-1">
              {assetKey
                ? `No logs for asset in the last ${hoursBack} hours`
                : `No logs for run ${runId}`}
            </p>
          </div>
        ) : (
          <div className="space-y-1 font-mono text-xs max-h-96 overflow-y-auto">
            {filteredLogs.map((log, idx) => (
              <div
                key={idx}
                className={cn(
                  'flex items-start gap-2 py-1 px-2 hover:bg-muted/50 rounded',
                  levelColors[log.level] || 'text-foreground',
                )}
              >
                {/* Level icon */}
                <span className="flex-shrink-0 mt-0.5">
                  {levelIcons[log.level] || levelIcons.info}
                </span>

                {/* Timestamp */}
                <span className="flex-shrink-0 text-muted-foreground w-20">
                  {formatDate(
                    log.timestamp,
                    settings?.ui?.dateFormat || 'relative',
                  )}
                </span>

                {/* Message */}
                <span className="flex-1 break-all">{log.message}</span>

                {/* Metadata badges */}
                {log.metadata.fn && (
                  <Badge variant="outline" className="text-xs flex-shrink-0">
                    {log.metadata.fn}
                  </Badge>
                )}
                {log.metadata.durationMs && (
                  <span className="text-muted-foreground flex-shrink-0">
                    {log.metadata.durationMs}ms
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

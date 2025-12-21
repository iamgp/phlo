/**
 * Materialization Timeline Component
 *
 * Vertical timeline showing materialization history for an asset.
 */

import { Badge } from '@/components/ui/badge'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import type { MaterializationEvent } from '@/server/dagster.server'
import { getMaterializationHistory } from '@/server/dagster.server'
import { formatDateTime } from '@/utils/dateFormat'
import { Link } from '@tanstack/react-router'
import {
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  ExternalLink,
  Loader2,
  Terminal,
  XCircle,
} from 'lucide-react'
import { useEffect, useState } from 'react'

interface MaterializationTimelineProps {
  assetKey: string
  limit?: number
}

export function MaterializationTimeline({
  assetKey,
  limit = 10,
}: MaterializationTimelineProps) {
  const [events, setEvents] = useState<Array<MaterializationEvent>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const { settings } = useObservatorySettings()

  useEffect(() => {
    async function loadHistory() {
      setLoading(true)
      setError(null)
      try {
        const result = await getMaterializationHistory({
          data: { assetKey, limit },
        })
        if ('error' in result) {
          setError(result.error)
        } else {
          setEvents(result)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history')
      } finally {
        setLoading(false)
      }
    }
    loadHistory()
  }, [assetKey, limit])

  const toggleExpand = (runId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(runId)) {
        next.delete(runId)
      } else {
        next.add(runId)
      }
      return next
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-primary animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-destructive">
        <XCircle className="w-8 h-8 mx-auto mb-2" />
        <p>{error}</p>
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No materializations yet</p>
        <p className="text-sm mt-1">Run a materialization to see history</p>
      </div>
    )
  }

  return (
    <div className="space-y-0">
      {events.map((event, idx) => {
        const isExpanded = expandedIds.has(event.runId)
        const timestamp = new Date(Number(event.timestamp))
        const isFirst = idx === 0

        return (
          <div key={`${event.runId}-${event.timestamp}`} className="relative">
            {/* Timeline line */}
            {idx < events.length - 1 && (
              <div className="absolute left-3.5 top-8 bottom-0 w-0.5 bg-border" />
            )}

            {/* Event */}
            <div className="flex gap-3 py-2">
              {/* Status indicator */}
              <div
                className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
                  event.status === 'SUCCESS'
                    ? 'bg-green-900/50'
                    : event.status === 'FAILURE'
                      ? 'bg-red-900/50'
                      : 'bg-yellow-900/50'
                }`}
              >
                {event.status === 'SUCCESS' ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : event.status === 'FAILURE' ? (
                  <XCircle className="w-4 h-4 text-red-400" />
                ) : (
                  <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <button
                  onClick={() => toggleExpand(event.runId)}
                  className="flex items-center gap-2 w-full text-left hover:bg-muted/50 rounded px-2 py-1 -mx-2 -my-1"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground">
                        {formatDateTime(timestamp, settings.ui.dateFormat)}
                      </span>
                      {isFirst && (
                        <Badge variant="secondary" className="text-xs">
                          Latest
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      Run: {event.runId.slice(0, 8)}...
                    </div>
                  </div>
                </button>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="mt-2 ml-6 space-y-2">
                    {/* Metadata */}
                    {event.metadata.length > 0 && (
                      <div className="space-y-1">
                        {event.metadata.slice(0, 5).map((m, midx) => (
                          <div
                            key={midx}
                            className="flex items-start gap-2 text-xs"
                          >
                            <span className="text-muted-foreground min-w-[80px]">
                              {m.key}:
                            </span>
                            <span className="text-foreground font-mono truncate">
                              {m.value}
                            </span>
                          </div>
                        ))}
                        {event.metadata.length > 5 && (
                          <div className="text-xs text-muted-foreground">
                            +{event.metadata.length - 5} more...
                          </div>
                        )}
                      </div>
                    )}

                    {/* Links */}
                    <div className="flex items-center gap-3">
                      <Link
                        to="/logs"
                        search={{
                          runId: event.runId,
                          service: undefined,
                          level: undefined,
                        }}
                        className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80"
                      >
                        <Terminal className="w-3 h-3" />
                        View Logs
                      </Link>
                      <a
                        href={`http://localhost:3000/runs/${event.runId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        View in Dagster
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

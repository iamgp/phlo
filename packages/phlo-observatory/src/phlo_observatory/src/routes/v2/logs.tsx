import { createFileRoute } from '@tanstack/react-router'
import { AlertCircle, FileText, Radio, Search, Terminal } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import type { V2LogEvent, V2LogFacets, V2ResourceResult } from '@/v2/api/types'
import { getV2LogFacets, getV2LogRecords } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/logs')({
  component: Logs,
})

function Logs() {
  const result = useLiveResource(getV2LogRecords)
  const logs = result.data ?? []
  const [level, setLevel] = useState('all')
  const [source, setSource] = useState('all')
  const [query, setQuery] = useState('')
  const [facets, setFacets] = useState<V2ResourceResult<V2LogFacets>>({
    data: null,
    error: null,
  })
  const sources = new Set(
    facets.data?.sources ?? logs.map((log) => log.source ?? 'platform'),
  )
  const levels = new Set(facets.data?.levels ?? logs.map((log) => log.level))
  const filtered = useMemo(
    () =>
      logs.filter(
        (log) =>
          (level === 'all' || log.level === level) &&
          (source === 'all' || (log.source ?? 'platform') === source) &&
          matchesLogQuery(log, query),
      ),
    [level, logs, query, source],
  )
  const latest = filtered[0] ?? null

  useEffect(() => {
    void getV2LogFacets().then(setFacets)
  }, [])

  return (
    <V2Page
      kicker="Logs"
      title="Evidence console"
      description="Recent events attached to services, assets, runs, and recovery actions."
      action={<span className="phlo-v2-pill">{sources.size} sources</span>}
    >
      <section className="phlo-v2-log-shell">
        <div className="phlo-v2-log-console">
          <div className="phlo-v2-console-toolbar phlo-v2-log-toolbar">
            <span className="phlo-v2-log-toolbar-title">
              <Terminal className="size-4" />
              Live tail
            </span>
            <span className="phlo-v2-pill">{filtered.length} events</span>
          </div>
          <div className="phlo-v2-filter-row">
            <label className="phlo-v2-search-field">
              <Search className="size-4" />
              <input
                aria-label="Search logs"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search evidence"
                value={query}
              />
            </label>
            <select
              value={source}
              onChange={(event) => setSource(event.target.value)}
            >
              <option value="all">All sources</option>
              {Array.from(sources).map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
            <select
              value={level}
              onChange={(event) => setLevel(event.target.value)}
            >
              <option value="all">All levels</option>
              {Array.from(levels).map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
          </div>
          <div className="phlo-v2-console-body">
            {filtered.map((log) => (
              <LogLine key={log.id} log={log} />
            ))}
            {filtered.length === 0 && (
              <div className="phlo-v2-empty-state">
                No log events returned yet.
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Evidence detail</div>
          {latest ? (
            <>
              <h2>{latest.source ?? 'platform'}</h2>
              <p>{latest.message}</p>
              <dl className="phlo-v2-facts">
                <Fact label="Level" value={latest.level} />
                <Fact
                  label="Resource"
                  value={latest.resource?.label ?? 'platform'}
                />
                <Fact label="Kind" value={latest.resource?.kind ?? 'event'} />
                <Fact
                  label="Timestamp"
                  value={latest.timestamp ?? 'not timestamped'}
                />
              </dl>
            </>
          ) : (
            <>
              <h2>No events</h2>
              <p>Connect a v2 telemetry read model to populate this console.</p>
            </>
          )}
          <div className="phlo-v2-detail-list">
            <div className="phlo-v2-mini-row">
              <span>Facets</span>
              <small>
                {sources.size} sources · {levels.size} levels ·{' '}
                {facets.data?.resources.length ?? 0} resources
              </small>
            </div>
          </div>
          {facets.error && (
            <div className="phlo-v2-panel-footer">{facets.error}</div>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
  )
}

function matchesLogQuery(log: V2LogEvent, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return [
    log.message,
    log.level,
    log.source,
    log.resource?.label,
    log.resource?.kind,
  ]
    .filter(Boolean)
    .some((value) => value!.toLowerCase().includes(needle))
}

function LogLine({ log }: { log: V2LogEvent }) {
  const Icon =
    log.level === 'error'
      ? AlertCircle
      : log.level === 'info'
        ? Radio
        : FileText

  return (
    <div className="phlo-v2-log-line">
      <span className="phlo-v2-log-time">{log.timestamp ?? '--:--:--'}</span>
      <span className="phlo-v2-log-level" data-level={log.level}>
        <Icon className="size-3.5" />
        {log.level}
      </span>
      <span className="phlo-v2-log-message">{log.message}</span>
      <span className="phlo-v2-log-source">
        {log.source ?? log.resource?.label ?? 'platform'}
      </span>
    </div>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

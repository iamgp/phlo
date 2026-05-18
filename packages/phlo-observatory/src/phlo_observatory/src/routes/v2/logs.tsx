import { Link, createFileRoute } from '@tanstack/react-router'
import { AlertCircle, FileText, Radio, Search, Terminal } from 'lucide-react'
import { useEffect, useMemo, useReducer } from 'react'

import type { V2LogEvent, V2LogFacets, V2ResourceResult } from '@/v2/api/types'
import { getV2LogFacets, getV2LogRecords } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { loadCachedResource, useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/logs')({
  component: Logs,
})

type LogsState = {
  facets: V2ResourceResult<V2LogFacets>
  level: string
  query: string
  selectedId: string | null
  source: string
}

type LogsAction =
  | { type: 'facets'; facets: V2ResourceResult<V2LogFacets> }
  | { type: 'level'; level: string }
  | { type: 'query'; query: string }
  | { type: 'selected'; selectedId: string | null }
  | { type: 'source'; source: string }

function logsReducer(state: LogsState, action: LogsAction): LogsState {
  switch (action.type) {
    case 'facets':
      return { ...state, facets: action.facets }
    case 'level':
      return { ...state, level: action.level }
    case 'query':
      return { ...state, query: action.query }
    case 'selected':
      return { ...state, selectedId: action.selectedId }
    case 'source':
      return { ...state, source: action.source }
  }
}

export function Logs() {
  const result = useLiveResource(getV2LogRecords, 120_000, 'v2:logs')
  const logs = result.data ?? []
  const [{ facets, level, query, selectedId, source }, dispatch] = useReducer(
    logsReducer,
    {
      data: null,
      error: null,
    },
    (initialFacets): LogsState => ({
      facets: initialFacets,
      level: 'all',
      query: '',
      selectedId: null,
      source: 'all',
    }),
  )
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
  const selected =
    filtered.find((log) => log.id === selectedId) ?? filtered[0] ?? null

  useEffect(() => {
    void loadCachedResource('v2:log-facets', getV2LogFacets, {
      staleMs: 120_000,
    }).then((nextFacets) => dispatch({ type: 'facets', facets: nextFacets }))
  }, [])

  return (
    <V2Page
      kicker="Logs"
      title="Evidence console"
      description="Filter recent events, open the full payload, and jump back to the affected resource."
      action={<span className="phlo-v2-pill">{sources.size} sources</span>}
    >
      <section className="phlo-v2-log-shell">
        <div className="phlo-v2-log-console">
          <div className="phlo-v2-console-toolbar phlo-v2-log-toolbar">
            <span className="phlo-v2-log-toolbar-title">
              <Terminal className="size-4" />
              Event stream
            </span>
            <span className="phlo-v2-pill">{filtered.length} events</span>
          </div>
          <div className="phlo-v2-filter-row">
            <label className="phlo-v2-search-field">
              <Search className="size-4" />
              <input
                aria-label="Search logs"
                onChange={(event) =>
                  dispatch({ type: 'query', query: event.target.value })
                }
                placeholder="Search evidence"
                value={query}
              />
            </label>
            <select
              value={source}
              onChange={(event) =>
                dispatch({ type: 'source', source: event.target.value })
              }
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
              onChange={(event) =>
                dispatch({ type: 'level', level: event.target.value })
              }
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
              <LogLine
                key={log.id}
                log={log}
                onSelect={(nextSelectedId) =>
                  dispatch({ type: 'selected', selectedId: nextSelectedId })
                }
                selected={log.id === selected?.id}
              />
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
          {selected ? (
            <>
              <h2>{selected.source ?? 'platform'}</h2>
              <p>{selected.message}</p>
              <dl className="phlo-v2-facts">
                <Fact label="Level" value={selected.level} />
                <Fact
                  label="Resource"
                  value={selected.resource?.label ?? 'platform'}
                />
                <Fact label="Kind" value={selected.resource?.kind ?? 'event'} />
                <Fact
                  label="Timestamp"
                  value={selected.timestamp ?? 'not timestamped'}
                />
              </dl>
              {selected.resource && routeForResource(selected.resource) && (
                <Link
                  className="phlo-v2-linked-resource"
                  to={routeForResource(selected.resource)!.to}
                  params={routeForResource(selected.resource)!.params}
                >
                  <FileText className="size-3.5" />
                  Open {selected.resource.kind}
                </Link>
              )}
              <div className="phlo-v2-detail-list">
                {Object.entries(selected.metadata).map(([key, value]) => (
                  <div className="phlo-v2-mini-row" key={key}>
                    <span>{key}</span>
                    <small>{formatLogValue(value)}</small>
                  </div>
                ))}
                {Object.keys(selected.metadata).length === 0 && (
                  <div className="phlo-v2-mini-row">
                    <span>Metadata</span>
                    <small>No structured fields returned</small>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <h2>No events</h2>
              <p>
                Logs will appear here as Phlo and stack services emit events.
              </p>
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

function routeForResource(
  resource: V2LogEvent['resource'],
):
  | { to: '/asset/$assetId'; params: { assetId: string } }
  | { to: '/table/$tableId'; params: { tableId: string } }
  | null {
  if (!resource) return null
  if (resource.kind === 'asset') {
    return { to: '/asset/$assetId', params: { assetId: resource.id } }
  }
  if (resource.kind === 'table') {
    return { to: '/table/$tableId', params: { tableId: resource.id } }
  }
  return null
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

function LogLine({
  log,
  onSelect,
  selected,
}: {
  log: V2LogEvent
  onSelect: (id: string) => void
  selected: boolean
}) {
  const Icon =
    log.level === 'error'
      ? AlertCircle
      : log.level === 'info'
        ? Radio
        : FileText

  return (
    <button
      className="phlo-v2-log-line"
      data-active={selected}
      onClick={() => onSelect(log.id)}
      type="button"
    >
      <span className="phlo-v2-log-time">{log.timestamp ?? '--:--:--'}</span>
      <span className="phlo-v2-log-level" data-level={log.level}>
        <Icon className="size-3.5" />
        {log.level}
      </span>
      <span className="phlo-v2-log-message">{log.message}</span>
      <span className="phlo-v2-log-source">
        {log.source ?? log.resource?.label ?? 'platform'}
      </span>
    </button>
  )
}

function formatLogValue(value: unknown): string {
  if (value === null || value === undefined) return 'unset'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return JSON.stringify(value)
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

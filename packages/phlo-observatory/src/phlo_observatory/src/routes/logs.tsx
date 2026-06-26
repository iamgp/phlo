import { Link, createFileRoute } from '@tanstack/react-router'
import { AlertCircle, FileText, Radio, Search, Terminal } from 'lucide-react'
import { useEffect, useMemo, useReducer } from 'react'

import type {
  ObservatoryLogEvent,
  ObservatoryLogFacets,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import {
  getObservatoryLogFacets,
  getObservatoryLogRecords,
} from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import {
  loadCachedResource,
  useLiveResource,
} from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/logs')({
  component: Logs,
})

type LogsState = {
  facets: ObservatoryResourceResult<ObservatoryLogFacets>
  level: string
  query: string
  selectedId: string | null
  source: string
}

type LogsAction =
  | { type: 'facets'; facets: ObservatoryResourceResult<ObservatoryLogFacets> }
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
  const result = useLiveResource(getObservatoryLogRecords, 120_000, 'v2:logs')
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
    void loadCachedResource('v2:log-facets', getObservatoryLogFacets, {
      staleMs: 120_000,
    }).then((nextFacets) => dispatch({ type: 'facets', facets: nextFacets }))
  }, [])

  return (
    <ObservatoryPage
      kicker="Logs"
      title="Evidence console"
      description="Filter recent events, open the full payload, and jump back to the affected resource."
      action={
        <span className="phlo-observatory-pill">{sources.size} sources</span>
      }
    >
      <section className="phlo-observatory-log-shell">
        <div className="phlo-observatory-log-console">
          <div className="phlo-observatory-console-toolbar phlo-observatory-log-toolbar">
            <span className="phlo-observatory-log-toolbar-title">
              <Terminal className="size-4" />
              Event stream
            </span>
            <span className="phlo-observatory-pill">
              {filtered.length} events
            </span>
          </div>
          <div className="phlo-observatory-filter-row">
            <label className="phlo-observatory-search-field">
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
          <div className="phlo-observatory-console-body">
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
              <div className="phlo-observatory-empty-state">
                No log events returned yet.
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-observatory-inspector">
          <div className="phlo-observatory-inspector-label">
            Evidence detail
          </div>
          {selected ? (
            <>
              <h2>{selected.source ?? 'platform'}</h2>
              <p>{selected.message}</p>
              <dl className="phlo-observatory-facts">
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
                  className="phlo-observatory-linked-resource"
                  to={routeForResource(selected.resource)!.to}
                  params={routeForResource(selected.resource)!.params}
                >
                  <FileText className="size-3.5" />
                  Open {selected.resource.kind}
                </Link>
              )}
              <div className="phlo-observatory-detail-list">
                {Object.entries(selected.metadata).map(([key, value]) => (
                  <div className="phlo-observatory-mini-row" key={key}>
                    <span>{key}</span>
                    <small>{formatLogValue(value)}</small>
                  </div>
                ))}
                {Object.keys(selected.metadata).length === 0 && (
                  <div className="phlo-observatory-mini-row">
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
          <div className="phlo-observatory-detail-list">
            <div className="phlo-observatory-mini-row">
              <span>Facets</span>
              <small>
                {sources.size} sources · {levels.size} levels ·{' '}
                {facets.data?.resources.length ?? 0} resources
              </small>
            </div>
          </div>
          {facets.error && (
            <div className="phlo-observatory-panel-footer">{facets.error}</div>
          )}
          {result.error && (
            <div className="phlo-observatory-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </ObservatoryPage>
  )
}

function routeForResource(
  resource: ObservatoryLogEvent['resource'],
):
  | { to: '/assets/$assetId'; params: { assetId: string } }
  | { to: '/data/$tableId'; params: { tableId: string } }
  | null {
  if (!resource) return null
  if (resource.kind === 'asset') {
    return { to: '/assets/$assetId', params: { assetId: resource.id } }
  }
  if (resource.kind === 'table') {
    return { to: '/data/$tableId', params: { tableId: resource.id } }
  }
  return null
}

function matchesLogQuery(log: ObservatoryLogEvent, query: string): boolean {
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
  log: ObservatoryLogEvent
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
      className="phlo-observatory-log-line"
      data-active={selected}
      onClick={() => onSelect(log.id)}
      type="button"
    >
      <span className="phlo-observatory-log-time">
        {log.timestamp ?? '--:--:--'}
      </span>
      <span className="phlo-observatory-log-level" data-level={log.level}>
        <Icon className="size-3.5" />
        {log.level}
      </span>
      <span className="phlo-observatory-log-message">{log.message}</span>
      <span className="phlo-observatory-log-source">
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

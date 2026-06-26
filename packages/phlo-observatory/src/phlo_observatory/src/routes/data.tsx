import { Link, createFileRoute } from '@tanstack/react-router'
import {
  Columns3,
  Database,
  GitBranch,
  Play,
  Rows3,
  Save,
  Search,
  Terminal,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryAsset,
  ObservatoryCapabilities,
  ObservatoryOperation,
  ObservatoryQualityCheck,
  ObservatoryResourceResult,
  ObservatoryTable,
  ObservatoryTablePreview,
} from '@/observatory/api/types'
import type { ObservatoryFlowEdge, ObservatoryFlowNode } from '@/observatory/components/ObservatoryFlowCanvas'
import {
  getObservatoryAssetRecords,
  getObservatoryCapabilities,
  getObservatoryOperationRecords,
  getObservatoryQualityRecords,
  getObservatorySavedQueries,
  getObservatoryTablePreview,
  getObservatoryTableRecords,
  runObservatoryQuery,
  saveObservatoryQuery,
} from '@/observatory/api/resources'
import { ObservatoryFlowCanvas } from '@/observatory/components/ObservatoryFlowCanvas'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import {
  loadCachedResource,
  readMetric,
  useLiveResource,
} from '@/observatory/routes/liveResource'

const previewLimit = 100

export const Route = createFileRoute('/data')({
  component: Data,
})

export function Data() {
  return useDataRoute()
}

function useDataRoute() {
  const result = useLiveResource(getObservatoryTableRecords, 120_000, 'v2:tables')
  const assetResult = useLiveResource(getObservatoryAssetRecords, 120_000, 'v2:assets')
  const qualityResult = useLiveResource(
    getObservatoryQualityRecords,
    120_000,
    'v2:quality',
  )
  const operationResult = useLiveResource(
    getObservatoryOperationRecords,
    120_000,
    'v2:operations',
  )
  const tables = result.data ?? []
  const hasLoadedTables = result.data !== null
  const assets = assetResult.data ?? []
  const quality = qualityResult.data ?? []
  const operations = operationResult.data ?? []
  const sortedTables = useMemo(() => sortTablesForFlow(tables), [tables])
  const [tableQuery, setTableQuery] = useState('')
  const filteredTables = useMemo(
    () => filterTables(sortedTables, tableQuery),
    [sortedTables, tableQuery],
  )
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    sortedTables.find((table) => table.id === selectedId) ??
    chooseDefaultTable(filteredTables.length ? filteredTables : sortedTables) ??
    null
  const [activeDetail, setActiveDetail] = useState<DataDetailTab>('sql')
  const [mainView, setMainView] = useState<DataMainView>('rows')
  const [previewRefreshKey, setPreviewRefreshKey] = useState(0)
  const [sql, setSql] = useState('')
  const [queryResult, setQueryResult] = useState<
    ObservatoryResourceResult<{
      columns: Array<string>
      rows: Array<Record<string, unknown>>
      effective_sql: string
      warnings: Array<string>
    }>
  >({ data: null, error: null })
  const [savedQueries, setSavedQueries] = useState<
    ObservatoryResourceResult<
      Array<{
        id: string
        name: string
        sql: string
        branch?: string | null
      }>
    >
  >({ data: [], error: null })
  const [preview, setPreview] = useState<ObservatoryResourceResult<ObservatoryTablePreview>>({
    data: null,
    error: null,
  })
  const [capabilities, setCapabilities] =
    useState<ObservatoryResourceResult<ObservatoryCapabilities> | null>(null)
  const [isLoadingMoreRows, setIsLoadingMoreRows] = useState(false)
  const namespaces = new Set(
    tables.map((table) => table.namespace ?? 'default'),
  )
  const graph = useMemo(() => buildTableGraph(tables, assets), [assets, tables])
  const branchesAvailable = capabilities?.data?.features.branches === true
  const selectedPreview =
    preview.data && selected && preview.data.table.id === selected.id
      ? preview.data
      : null
  const selectedProfile = useMemo(
    () =>
      selected
        ? buildTableProfile(
            selected,
            selectedPreview,
            assets,
            quality,
            operations,
          )
        : null,
    [assets, operations, quality, selected, selectedPreview],
  )
  const selectedPreviewError = selectedPreview ? preview.error : null
  const selectedRowCount =
    selectedPreview && selected ? selectedPreview.row_count : null
  const applySelectedPreview = useCallback(
    (nextSql: string, nextPreview: ObservatoryResourceResult<ObservatoryTablePreview>) => {
      setSql(nextSql)
      setPreview(nextPreview)
    },
    [],
  )
  const applyPreview = useCallback(
    (nextPreview: ObservatoryResourceResult<ObservatoryTablePreview>) => setPreview(nextPreview),
    [],
  )

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    let retryTimer: number | undefined
    setPreview({ data: null, error: null })
    const key = `v2:table-preview:${selected.id}:${previewLimit}:0:${previewRefreshKey}`
    const loadPreview = (force = false) =>
      loadCachedResource(
        key,
        () =>
          getObservatoryTablePreview({
            data: { tableId: selected.id, limit: previewLimit, offset: 0 },
          }),
        {
          force,
          staleMs: 120_000,
        },
      )

    void loadPreview(previewRefreshKey > 0).then((next) => {
      if (cancelled) return
      applySelectedPreview(defaultSqlForTable(selected), next)
      if (isTransientPreviewMiss(next.error)) {
        retryTimer = window.setTimeout(() => {
          void loadPreview(true).then((retry) => {
            if (!cancelled) applyPreview(retry)
          })
        }, 750)
      }
    })
    return () => {
      cancelled = true
      if (retryTimer !== undefined) window.clearTimeout(retryTimer)
    }
  }, [applyPreview, applySelectedPreview, previewRefreshKey, selected])

  const loadMoreRows = useCallback(() => {
    if (!selected || isLoadingMoreRows) return
    const current = selectedPreview
    if (!current?.has_more) return
    const offset = current.rows.length
    setIsLoadingMoreRows(true)
    const key = `v2:table-preview:${selected.id}:${previewLimit}:${offset}:${previewRefreshKey}`
    void loadCachedResource(
      key,
      () =>
        getObservatoryTablePreview({
          data: { tableId: selected.id, limit: previewLimit, offset },
        }),
      { staleMs: 120_000 },
    ).then((next) => {
      setIsLoadingMoreRows(false)
      setPreview((existing) => {
        if (next.error || !next.data) {
          return { data: existing.data, error: next.error }
        }
        if (!existing.data) return next
        if (existing.data.table.id !== next.data.table.id) return existing
        return {
          data: mergeTablePreviews(existing.data, next.data),
          error: null,
        }
      })
    })
  }, [isLoadingMoreRows, previewRefreshKey, selected, selectedPreview])

  useEffect(() => {
    void loadCachedResource('v2:saved-queries', getObservatorySavedQueries, {
      staleMs: 300_000,
    }).then(setSavedQueries)
    void loadCachedResource('v2:capabilities', getObservatoryCapabilities, {
      staleMs: 120_000,
    }).then(setCapabilities)
  }, [])

  return (
    <ObservatoryPage
      kicker="Data"
      title="Table browser"
      description={
        branchesAvailable
          ? 'Browse tables, branches, schemas, and row-journey entry points.'
          : 'Browse tables, schemas, preview rows, and row-journey entry points.'
      }
      action={
        <span className="phlo-observatory-pill">{namespaces.size} namespaces</span>
      }
    >
      <section className="phlo-observatory-browser-shell">
        <div className="phlo-observatory-table-browser">
          <div className="phlo-observatory-browser-toolbar">
            <span>
              <Database className="size-4" />
              Table browser
            </span>
            <label className="phlo-observatory-search-field phlo-observatory-data-search">
              <Search className="size-4" />
              <input
                aria-label="Search tables"
                onChange={(event) => setTableQuery(event.target.value)}
                placeholder={
                  branchesAvailable
                    ? 'Search name, namespace, branch'
                    : 'Search name, namespace, schema'
                }
                value={tableQuery}
              />
            </label>
            <span className="phlo-observatory-pill">
              {filteredTables.length} / {tables.length} tables
            </span>
          </div>
          <div
            className="phlo-observatory-table-grid"
            data-branches={branchesAvailable}
            role="table"
          >
            <div className="phlo-observatory-table-head" role="row">
              <span>Name</span>
              <span>Namespace</span>
              <span>Format</span>
              {branchesAvailable && <span>Branch</span>}
              <span>Rows</span>
              <span>Catalog</span>
            </div>
            {filteredTables.map((table) => (
              <button
                className="phlo-observatory-table-row"
                data-active={table.id === selected?.id}
                key={table.id}
                onClick={() => setSelectedId(table.id)}
                role="row"
                type="button"
              >
                <span>{table.name}</span>
                <span>{table.namespace ?? 'default'}</span>
                <span>{table.format ?? 'unknown'}</span>
                {branchesAvailable && <span>{table.branch ?? 'main'}</span>}
                <span>
                  {table.id === selected?.id && selectedRowCount !== null
                    ? selectedRowCount
                    : (readTableRecordCount(table) ?? '—')}
                </span>
                <span>{tableCatalogState(table)}</span>
              </button>
            ))}
            {filteredTables.length === 0 && (
              <div className="phlo-observatory-empty-state">
                {!hasLoadedTables
                  ? 'Loading tables…'
                  : tables.length === 0
                    ? 'No tables registered yet.'
                    : 'No tables match this filter.'}
              </div>
            )}
          </div>
          {selected && selectedProfile && (
            <DataProfileBand profile={selectedProfile} selected={selected} />
          )}
          <div className="phlo-observatory-data-main-tabs" role="tablist">
            {dataMainViews.map((view) => (
              <button
                aria-selected={mainView === view.id}
                data-active={mainView === view.id}
                key={view.id}
                onClick={() => setMainView(view.id)}
                role="tab"
                type="button"
              >
                {view.icon}
                {view.label}
              </button>
            ))}
          </div>
          {mainView === 'flow' ? (
            <div className="phlo-observatory-flow-band">
              <div className="phlo-observatory-workspace-toolbar">
                <span>Lakehouse table flow</span>
                <span className="phlo-observatory-pill">
                  {graph.edges.length} bindings
                </span>
              </div>
              <ObservatoryFlowCanvas
                edges={graph.edges}
                nodes={graph.nodes}
                onSelect={setSelectedId}
                selectedId={selected?.id}
              />
            </div>
          ) : (
            <DataPreviewTable
              isLoadingMoreRows={isLoadingMoreRows}
              onLoadMoreRows={loadMoreRows}
              mode={mainView}
              preview={selectedPreview}
              selected={selected}
            />
          )}
        </div>

        <aside className="phlo-observatory-inspector">
          <div className="phlo-observatory-inspector-label">Table inspector</div>
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p>{selected.asset_id ?? 'No asset binding returned.'}</p>
              <dl className="phlo-observatory-facts">
                <Fact label="Schema" value={selected.schema_name ?? 'n/a'} />
                <Fact
                  label="Namespace"
                  value={selected.namespace ?? 'default'}
                />
                <Fact label="Format" value={selected.format ?? 'unknown'} />
                {branchesAvailable && (
                  <Fact label="Branch" value={selected.branch ?? 'main'} />
                )}
                <Fact label="Catalog" value={tableCatalogState(selected)} />
              </dl>
              <div className="phlo-observatory-mini-preview">
                <div>
                  <Rows3 className="size-4" />
                  {selectedPreview?.row_count ??
                    readMetric(selected.metadata, 'records') ??
                    'Profile pending'}{' '}
                  records
                </div>
                <div>
                  <Columns3 className="size-4" />
                  {selectedPreview?.columns.length
                    ? selectedPreview.columns.length
                    : 'Profile pending'}{' '}
                  columns
                </div>
              </div>
              <div
                className="phlo-observatory-tab-row"
                role="tablist"
                aria-label="Table detail"
              >
                {dataDetailTabs.map((tab) => (
                  <button
                    aria-selected={activeDetail === tab.id}
                    data-active={activeDetail === tab.id}
                    key={tab.id}
                    onClick={() => setActiveDetail(tab.id)}
                    role="tab"
                    type="button"
                  >
                    {tab.icon}
                    {tab.label}
                  </button>
                ))}
              </div>
              <DataDetailPanel
                active={activeDetail}
                preview={selectedPreview}
                queryResult={queryResult}
                selected={selected}
                onRefresh={() => setPreviewRefreshKey((key) => key + 1)}
                onRunQuery={(nextSql) => {
                  const request = {
                    sql: nextSql,
                    limit: 100,
                    ...(branchesAvailable
                      ? { branch: selected.branch ?? 'main' }
                      : {}),
                  }
                  void runObservatoryQuery({
                    data: request,
                  }).then(setQueryResult)
                }}
                onSaveQuery={(nextSql) => {
                  const name = window.prompt('Saved query name')
                  if (!name) return
                  const request = {
                    name,
                    sql: nextSql,
                    ...(branchesAvailable
                      ? { branch: selected.branch ?? 'main' }
                      : {}),
                  }
                  void saveObservatoryQuery({
                    data: request,
                  }).then((next) => {
                    if (next.data) {
                      setSavedQueries((current) => ({
                        data: [next.data!, ...(current.data ?? [])],
                        error: null,
                      }))
                    } else {
                      setSavedQueries((current) => ({
                        data: current.data,
                        error: next.error,
                      }))
                    }
                  })
                }}
                savedQueries={savedQueries.data ?? []}
                showBranch={branchesAvailable}
                setSql={setSql}
                sql={sql}
              />
              {selectedPreviewError && (
                <div className="phlo-observatory-panel-footer">
                  {selectedPreviewError}
                </div>
              )}
            </>
          ) : (
            <p>No table selected.</p>
          )}
          {result.error && (
            <div className="phlo-observatory-panel-footer">{result.error}</div>
          )}
          {qualityResult.error && (
            <div className="phlo-observatory-panel-footer">{qualityResult.error}</div>
          )}
          {operationResult.error && (
            <div className="phlo-observatory-panel-footer">{operationResult.error}</div>
          )}
        </aside>
      </section>
    </ObservatoryPage>
  )
}

type DataDetailTab = 'preview' | 'sql' | 'journey'
type DataMainView = 'rows' | 'schema' | 'flow'

const dataMainViews: Array<{
  id: DataMainView
  label: string
  icon: ReactNode
}> = [
  { id: 'rows', label: 'Rows', icon: <Rows3 className="size-3.5" /> },
  { id: 'schema', label: 'Schema', icon: <Columns3 className="size-3.5" /> },
  { id: 'flow', label: 'Flow', icon: <GitBranch className="size-3.5" /> },
]

const dataDetailTabs: Array<{
  id: DataDetailTab
  label: string
  icon: ReactNode
}> = [
  { id: 'preview', label: 'Preview', icon: <Rows3 className="size-3.5" /> },
  { id: 'sql', label: 'SQL', icon: <Terminal className="size-3.5" /> },
  { id: 'journey', label: 'Journey', icon: <GitBranch className="size-3.5" /> },
]

type TableProfile = {
  stage: string
  records: string | number | boolean | null
  columns: number | null
  upstream: number
  downstream: number
  qualityLabel: string
  qualityState: 'ok' | 'warning' | 'error' | 'unknown'
  latestOperation: ObservatoryOperation | null
  businessKeys: Array<string>
}

function DataProfileBand({
  profile,
  selected,
}: {
  profile: TableProfile
  selected: ObservatoryTable
}) {
  return (
    <div className="phlo-observatory-data-profile" data-state={profile.qualityState}>
      <div className="phlo-observatory-data-profile-stage">
        <span>Stage</span>
        <strong>{profile.stage}</strong>
        <small>{selected.namespace ?? selected.schema_name ?? 'default'}</small>
      </div>
      <div className="phlo-observatory-data-profile-grid">
        <ProfileFact label="Records" value={profile.records ?? 'pending'} />
        <ProfileFact label="Columns" value={profile.columns ?? 'pending'} />
        <ProfileFact
          label="Lineage"
          value={`${profile.upstream} up / ${profile.downstream} down`}
        />
        <ProfileFact label="Quality" value={profile.qualityLabel} />
        <ProfileFact
          label="Latest event"
          value={profile.latestOperation?.name ?? 'No operation linked'}
        />
      </div>
      <div className="phlo-observatory-data-profile-keys">
        {profile.businessKeys.length > 0 ? (
          profile.businessKeys.map((key) => (
            <span className="phlo-observatory-pill" key={key}>
              {key}
            </span>
          ))
        ) : (
          <span className="phlo-observatory-pill">No key columns detected</span>
        )}
      </div>
    </div>
  )
}

function ProfileFact({
  label,
  value,
}: {
  label: string
  value: string | number | boolean
}) {
  return (
    <div className="phlo-observatory-data-profile-fact">
      <span>{label}</span>
      <strong>{String(value)}</strong>
    </div>
  )
}

function DataPreviewTable({
  isLoadingMoreRows,
  mode,
  onLoadMoreRows,
  preview,
  selected,
}: {
  isLoadingMoreRows: boolean
  mode: Exclude<DataMainView, 'flow'>
  onLoadMoreRows: () => void
  preview: ObservatoryTablePreview | null
  selected: ObservatoryTable | null
}) {
  const columns = preview?.columns ?? []
  const rows = preview?.rows ?? []

  if (!selected) {
    return (
      <div className="phlo-observatory-data-preview-empty">
        Select a table to inspect rows and schema.
      </div>
    )
  }

  if (mode === 'schema') {
    return (
      <div className="phlo-observatory-data-preview">
        <div className="phlo-observatory-workspace-toolbar">
          <span>
            <Columns3 className="size-4" />
            {selected.name} schema
          </span>
          <span className="phlo-observatory-pill">{columns.length} columns</span>
        </div>
        <div className="phlo-observatory-schema-grid" role="table">
          <div className="phlo-observatory-schema-head" role="row">
            <span>Column</span>
            <span>Type</span>
          </div>
          {columns.map((column, index) => (
            <div className="phlo-observatory-schema-row" key={column} role="row">
              <span>{column}</span>
              <span>{columnTypeFor(preview, column, index)}</span>
            </div>
          ))}
          {columns.length === 0 && (
            <div className="phlo-observatory-empty-state">
              No schema preview returned yet.
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="phlo-observatory-data-preview">
      <div className="phlo-observatory-workspace-toolbar">
        <span>
          <Rows3 className="size-4" />
          {selected.name} rows
        </span>
        <span className="phlo-observatory-pill">
          {rows.length} loaded
          {preview?.row_count ? ` · ${preview.row_count} total` : ''}
        </span>
      </div>
      {columns.length > 0 ? (
        <div
          className="phlo-observatory-row-preview-scroll"
          onScroll={(event) => {
            const target = event.currentTarget
            const remaining =
              target.scrollHeight - target.scrollTop - target.clientHeight
            if (remaining < 96) onLoadMoreRows()
          }}
        >
          <table className="phlo-observatory-row-preview-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={String(row._phlo_row_id ?? index)}>
                  {columns.map((column) => (
                    <td key={column}>{formatCell(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {(preview?.has_more || isLoadingMoreRows) && (
            <button
              className="phlo-observatory-row-preview-more"
              disabled={isLoadingMoreRows}
              onClick={onLoadMoreRows}
              type="button"
            >
              {isLoadingMoreRows ? 'Loading more rows…' : 'Load more rows'}
            </button>
          )}
        </div>
      ) : (
        <div className="phlo-observatory-data-preview-empty">
          {preview ? previewEmptyCopy(selected) : 'Loading preview rows…'}
        </div>
      )}
    </div>
  )
}

function mergeTablePreviews(
  current: ObservatoryTablePreview,
  next: ObservatoryTablePreview,
): ObservatoryTablePreview {
  return {
    ...next,
    columns: next.columns.length ? next.columns : current.columns,
    column_types: next.column_types.length
      ? next.column_types
      : current.column_types,
    offset: current.offset,
    rows: [...current.rows, ...next.rows],
  }
}

function columnTypeFor(
  preview: ObservatoryTablePreview | null,
  column: string,
  index: number,
): string {
  const explicitType = preview?.column_types?.[index]
  if (typeof explicitType === 'string' && explicitType.trim()) {
    return explicitType
  }

  const sampledValue = preview?.rows.find(
    (row) => row[column] !== null && row[column] !== undefined,
  )?.[column]
  if (typeof sampledValue === 'number') {
    return Number.isInteger(sampledValue) ? 'integer' : 'double'
  }
  if (typeof sampledValue === 'boolean') {
    return 'boolean'
  }
  if (typeof sampledValue === 'string') {
    return 'varchar'
  }
  if (Array.isArray(sampledValue)) {
    return 'array'
  }
  if (typeof sampledValue === 'object' && sampledValue !== null) {
    return 'object'
  }
  return 'unknown'
}

function DataDetailPanel({
  active,
  onRefresh,
  onRunQuery,
  onSaveQuery,
  preview,
  queryResult,
  savedQueries,
  selected,
  showBranch,
  setSql,
  sql,
}: {
  active: DataDetailTab
  onRefresh: () => void
  onRunQuery: (sql: string) => void
  onSaveQuery: (sql: string) => void
  preview: ObservatoryTablePreview | null
  queryResult: ObservatoryResourceResult<{
    columns: Array<string>
    rows: Array<Record<string, unknown>>
    effective_sql: string
    warnings: Array<string>
  }>
  savedQueries: Array<{
    id: string
    name: string
    sql: string
    branch?: string | null
  }>
  selected: ObservatoryTable
  showBranch: boolean
  setSql: (value: string) => void
  sql: string
}) {
  if (active === 'sql') {
    return (
      <div className="phlo-observatory-query-panel">
        <div className="phlo-observatory-workspace-toolbar">
          <span>Preview query</span>
          <span className="phlo-observatory-pill">
            {preview?.limit ?? previewLimit} row limit
          </span>
        </div>
        <textarea
          onChange={(event) => setSql(event.target.value)}
          value={sql}
        />
        <div className="phlo-observatory-action-row">
          <button onClick={() => onRunQuery(sql)} type="button">
            <Play className="size-3.5" />
            Run query
          </button>
          <button onClick={onRefresh} type="button">
            <Play className="size-3.5" />
            Refresh preview
          </button>
          <button onClick={() => onSaveQuery(sql)} type="button">
            <Save className="size-3.5" />
            Save
          </button>
        </div>
        {savedQueries.length > 0 && (
          <div className="phlo-observatory-detail-list">
            {savedQueries.slice(0, 4).map((query) => (
              <button
                className="phlo-observatory-mini-row"
                key={query.id}
                onClick={() => setSql(query.sql)}
                type="button"
              >
                <span>{query.name}</span>
                <small>{showBranch ? (query.branch ?? 'main') : 'saved'}</small>
              </button>
            ))}
          </div>
        )}
        {queryResult.data && (
          <div className="phlo-observatory-detail-list">
            <div className="phlo-observatory-mini-row">
              <span>Effective SQL</span>
              <small>{queryResult.data.effective_sql}</small>
            </div>
            <div className="phlo-observatory-mini-row">
              <span>Rows</span>
              <small>{queryResult.data.rows.length}</small>
            </div>
          </div>
        )}
        {queryResult.error && (
          <div className="phlo-observatory-panel-footer">{queryResult.error}</div>
        )}
      </div>
    )
  }

  if (active === 'journey') {
    return (
      <div className="phlo-observatory-detail-list">
        <div className="phlo-observatory-mini-row">
          <span>Asset binding</span>
          <small>{selected.asset_id ?? 'none'}</small>
        </div>
        <div className="phlo-observatory-mini-row">
          <span>Namespace</span>
          <small>{selected.namespace ?? 'default'}</small>
        </div>
        <div className="phlo-observatory-mini-row">
          <span>Preview rows</span>
          <small>
            {preview
              ? `${preview.rows.length} loaded${preview.has_more ? ' · more available' : ''}`
              : 'Preview not loaded'}
          </small>
        </div>
        {showBranch && (
          <div className="phlo-observatory-mini-row">
            <span>Branch</span>
            <small>{selected.branch ?? 'main'}</small>
          </div>
        )}
        {selected.asset_id && (
          <Link
            className="phlo-observatory-mini-row"
            to="/asset/$assetId"
            params={{ assetId: selected.asset_id }}
          >
            <span>Open asset</span>
            <small>{selected.asset_id}</small>
          </Link>
        )}
      </div>
    )
  }

  return (
    <div className="phlo-observatory-detail-list">
      {(preview?.rows ?? []).slice(0, 4).map((row, index) => (
        <div
          className="phlo-observatory-mini-row phlo-observatory-mini-row-stack"
          key={String(row._phlo_row_id ?? index)}
        >
          <span>{String(row._phlo_row_id ?? `row-${index + 1}`)}</span>
          <small>
            {Object.entries(row)
              .filter(([key]) => key !== '_phlo_row_id')
              .slice(0, 3)
              .map(([key, value]) => `${key}: ${String(value)}`)
              .join(' · ')}
          </small>
        </div>
      ))}
      {(preview?.rows ?? []).length === 0 &&
        (preview?.columns ?? []).slice(0, 6).map((column) => (
          <div className="phlo-observatory-mini-row" key={column}>
            <span>{column}</span>
            <small>column</small>
          </div>
        ))}
      {preview && preview.columns.length === 0 && (
        <p>No column preview returned yet.</p>
      )}
    </div>
  )
}

function buildTableGraph(
  tables: Array<ObservatoryTable>,
  assets: Array<ObservatoryAsset>,
): {
  nodes: Array<ObservatoryFlowNode>
  edges: Array<ObservatoryFlowEdge>
} {
  const tableByAsset = new Map<string, ObservatoryTable>()
  for (const table of tables) {
    if (table.asset_id) {
      tableByAsset.set(table.asset_id, table)
    }
  }
  const assetById = new Map(assets.map((asset) => [asset.id, asset]))

  const tableNodes = sortTablesForFlow(tables).map(
    (table): ObservatoryFlowNode => ({
      id: table.id,
      label: table.name,
      kind: 'table',
      lane: tableLane(table),
      subtitle: table.namespace ?? table.schema_name,
      metric: table.format ?? 'table',
    }),
  )

  const edges = tables.flatMap((table): Array<ObservatoryFlowEdge> => {
    if (!table.asset_id) return []
    const asset = assetById.get(table.asset_id)
    if (!asset) return []
    const dependencyEdges: Array<ObservatoryFlowEdge> = []
    for (const dependencyId of asset.dependencies) {
      const dependency = tableByAsset.get(dependencyId)
      if (!dependency) continue
      dependencyEdges.push({
        id: `${dependency.id}->${table.id}`,
        source: dependency.id,
        target: table.id,
      })
    }
    return dependencyEdges
  })

  return { nodes: tableNodes, edges }
}

function sortTablesForFlow(tables: Array<ObservatoryTable>): Array<ObservatoryTable> {
  return tables.slice().sort((left, right) => {
    const leftLane = tableLane(left)
    const rightLane = tableLane(right)
    if (leftLane !== rightLane) {
      return laneRank(leftLane) - laneRank(rightLane)
    }
    return left.name.localeCompare(right.name)
  })
}

function chooseDefaultTable(tables: Array<ObservatoryTable>): ObservatoryTable | null {
  return (
    tables.find(
      (table) =>
        tableCatalogState(table) === 'Queryable' && tableLane(table) === 'gold',
    ) ??
    tables.find((table) => tableLane(table) === 'gold') ??
    tables.find(
      (table) =>
        tableCatalogState(table) === 'Queryable' &&
        readTableRecordCount(table) !== null,
    ) ??
    tables.find(
      (table) =>
        tableCatalogState(table) === 'Queryable' &&
        tableLane(table) === 'silver',
    ) ??
    tables.find((table) => tableCatalogState(table) === 'Queryable') ??
    tables.find((table) => tableLane(table) === 'silver') ??
    tables[0] ??
    null
  )
}

function readTableRecordCount(
  table: ObservatoryTable,
): string | number | boolean | null {
  return (
    readMetric(table.metadata, 'rows') ??
    readMetric(table.metadata, 'records') ??
    readMetric(table.metadata, 'row_count')
  )
}

function filterTables(tables: Array<ObservatoryTable>, query: string): Array<ObservatoryTable> {
  const needle = query.trim().toLowerCase()
  if (!needle) return tables
  return tables.filter((table) =>
    [
      table.name,
      table.id,
      table.namespace,
      table.schema_name,
      table.format,
      table.branch,
      table.asset_id,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle)),
  )
}

function isTransientPreviewMiss(error: string | null): boolean {
  return error?.toLowerCase().includes('table not found') ?? false
}

function tableCatalogState(table: ObservatoryTable): string {
  const state = readMetric(table.metadata, 'catalog_state')
  if (state === 'queryable') return 'Queryable'
  if (state === 'model_only') return 'Model only'

  const present = table.metadata.catalog_present
  if (present === true) return 'Queryable'
  if (present === false) return 'Model only'

  return 'Catalog'
}

function previewEmptyCopy(table: ObservatoryTable): string {
  if (tableCatalogState(table) === 'Model only') {
    return 'This model is registered, but it is not materialized in the active query catalog.'
  }
  return 'Preview rows are unavailable.'
}

function defaultSqlForTable(table: ObservatoryTable): string {
  return `select * from ${table.id} limit ${previewLimit}`
}

function buildTableProfile(
  table: ObservatoryTable,
  preview: ObservatoryTablePreview | null,
  assets: Array<ObservatoryAsset>,
  quality: Array<ObservatoryQualityCheck>,
  operations: Array<ObservatoryOperation>,
): TableProfile {
  const asset = table.asset_id
    ? assets.find((candidate) => candidate.id === table.asset_id)
    : null
  const dependencies = new Set(asset?.dependencies ?? [])
  const downstream = assets.filter((candidate) =>
    candidate.dependencies.includes(asset?.id ?? ''),
  )
  const checks = quality.filter((check) => check.asset_id === asset?.id)
  const linkedOperations = operations
    .filter((operation) => operationMatchesTable(operation, table, asset))
    .sort((left, right) =>
      operationTimestamp(right).localeCompare(operationTimestamp(left)),
    )
  const qualityState = checks.some((check) => check.status === 'failing')
    ? 'error'
    : checks.some((check) => check.status === 'warning' || check.blocking)
      ? 'warning'
      : checks.length > 0
        ? 'ok'
        : 'unknown'

  return {
    stage: stageLabelForTable(table, asset),
    records:
      preview?.row_count ??
      readTableRecordCount(table) ??
      readMetric(asset?.metadata ?? {}, 'records') ??
      null,
    columns: preview?.columns.length ?? readNumber(table.metadata.columns),
    upstream: dependencies.size,
    downstream: downstream.length,
    qualityLabel:
      checks.length === 0
        ? 'No checks'
        : `${checks.filter((check) => check.status === 'passing').length}/${checks.length} passing`,
    qualityState,
    latestOperation: linkedOperations[0] ?? null,
    businessKeys: detectBusinessKeys(preview, table),
  }
}

function operationMatchesTable(
  operation: ObservatoryOperation,
  table: ObservatoryTable,
  asset: ObservatoryAsset | null | undefined,
): boolean {
  const haystack = [
    operation.target?.id,
    operation.target?.label,
    operation.kind,
    operation.name,
    ...Object.values(operation.metadata).map((value) => String(value)),
  ]
    .join(' ')
    .toLowerCase()
  return [table.id, table.name, table.asset_id, asset?.id, asset?.name]
    .filter(Boolean)
    .some((value) => haystack.includes(String(value).toLowerCase()))
}

function operationTimestamp(operation: ObservatoryOperation): string {
  return operation.completed_at ?? operation.started_at ?? operation.id
}

function detectBusinessKeys(
  preview: ObservatoryTablePreview | null,
  table: ObservatoryTable,
): Array<string> {
  const columns = preview?.columns ?? []
  const explicit = [
    'experiment_id',
    'export_id',
    'plate_id',
    'assay_type',
    'id',
  ]
  const matches = explicit.filter((key) =>
    columns.some((column) => column.toLowerCase() === key),
  )
  if (matches.length > 0) return matches.slice(0, 4)
  const name = table.name.toLowerCase()
  if (name.includes('release')) return ['release metrics']
  if (name.includes('sample')) return ['sample keys']
  return columns
    .filter((column) => column.toLowerCase().endsWith('_id'))
    .slice(0, 4)
}

function stageLabelForTable(table: ObservatoryTable, asset: ObservatoryAsset | null | undefined) {
  const stage =
    readMetric(table.metadata, 'stage') ??
    readMetric(asset?.metadata ?? {}, 'stage') ??
    tableLane(table)
  return String(stage).charAt(0).toUpperCase() + String(stage).slice(1)
}

function readNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'string') return value
  if (
    typeof value === 'number' ||
    typeof value === 'boolean' ||
    typeof value === 'bigint'
  ) {
    return String(value)
  }
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

function tableLane(table: ObservatoryTable): string {
  const namespace = (table.namespace ?? '').toLowerCase()
  const name = table.name.toLowerCase()
  if (namespace === 'nightscout' || name.startsWith('dlt_')) return 'raw'
  if (namespace === 'bronze' || name.startsWith('stg_')) return 'bronze'
  if (namespace === 'silver') return 'silver'
  if (namespace === 'gold') return 'gold'
  if (namespace === 'marts' || name.startsWith('mrt_')) return 'marts'
  return 'table'
}

function laneRank(lane: string): number {
  return ['raw', 'bronze', 'silver', 'gold', 'marts', 'table'].indexOf(lane)
}

function Fact({
  label,
  value,
}: {
  label: string
  value: string | number | boolean
}) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{String(value)}</dd>
    </>
  )
}

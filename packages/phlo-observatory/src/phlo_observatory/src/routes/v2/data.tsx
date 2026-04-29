import { createFileRoute } from '@tanstack/react-router'
import {
  Columns3,
  Database,
  GitBranch,
  Play,
  Rows3,
  Save,
  Terminal,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { V2ResourceResult, V2Table, V2TablePreview } from '@/v2/api/types'
import type { V2FlowEdge, V2FlowNode } from '@/v2/components/V2FlowCanvas'
import { getV2TablePreview, getV2TableRecords } from '@/v2/api/resources'
import { V2FlowCanvas } from '@/v2/components/V2FlowCanvas'
import { V2Page } from '@/v2/components/V2Page'
import { readMetric, useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/data')({
  component: Data,
})

function Data() {
  const result = useLiveResource(getV2TableRecords)
  const tables = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    tables.find((table) => table.id === selectedId) ?? tables[0] ?? null
  const [activeDetail, setActiveDetail] = useState<DataDetailTab>('preview')
  const [sql, setSql] = useState('select * from selected_table limit 100')
  const [preview, setPreview] = useState<V2ResourceResult<V2TablePreview>>({
    data: null,
    error: null,
  })
  const namespaces = new Set(
    tables.map((table) => table.namespace ?? 'default'),
  )
  const graph = useMemo(() => buildTableGraph(tables), [tables])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getV2TablePreview({ data: { tableId: selected.id, limit: 50 } }).then(
      (next) => {
        if (!cancelled) setPreview(next)
      },
    )
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <V2Page
      kicker="Data"
      title="Tables, branches, and schemas."
      description="Browse the lakehouse inventory exposed by phlo-api v2."
      action={
        <span className="phlo-v2-pill">{namespaces.size} namespaces</span>
      }
    >
      <section className="phlo-v2-browser-shell">
        <div className="phlo-v2-table-browser">
          <div className="phlo-v2-flow-band">
            <div className="phlo-v2-workspace-toolbar">
              <span>Namespace map</span>
              <span className="phlo-v2-pill">
                {graph.edges.length} bindings
              </span>
            </div>
            <V2FlowCanvas
              edges={graph.edges}
              nodes={graph.nodes}
              onSelect={setSelectedId}
              selectedId={selected?.id}
            />
          </div>
          <div className="phlo-v2-browser-toolbar">
            <span>
              <Database className="size-4" />
              Table browser
            </span>
            <span className="phlo-v2-pill">{tables.length} tables</span>
          </div>
          <div className="phlo-v2-table-grid" role="table">
            <div className="phlo-v2-table-head" role="row">
              <span>Name</span>
              <span>Namespace</span>
              <span>Format</span>
              <span>Branch</span>
              <span>Rows</span>
              <span>Freshness</span>
            </div>
            {tables.map((table) => (
              <button
                className="phlo-v2-table-row"
                data-active={table.id === selected?.id}
                key={table.id}
                onClick={() => setSelectedId(table.id)}
                role="row"
                type="button"
              >
                <span>{table.name}</span>
                <span>{table.namespace ?? 'default'}</span>
                <span>{table.format ?? 'unknown'}</span>
                <span>{table.branch ?? 'main'}</span>
                <span>{readMetric(table.metadata, 'records') ?? 'n/a'}</span>
                <span>{readMetric(table.metadata, 'freshness') ?? 'n/a'}</span>
              </button>
            ))}
            {tables.length === 0 && (
              <div className="phlo-v2-empty-state">
                No tables registered by phlo-api v2.
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Table inspector</div>
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p>{selected.asset_id ?? 'No asset binding returned.'}</p>
              <dl className="phlo-v2-facts">
                <Fact label="Schema" value={selected.schema_name ?? 'n/a'} />
                <Fact
                  label="Namespace"
                  value={selected.namespace ?? 'default'}
                />
                <Fact label="Format" value={selected.format ?? 'unknown'} />
                <Fact label="Branch" value={selected.branch ?? 'main'} />
              </dl>
              <div className="phlo-v2-mini-preview">
                <div>
                  <Rows3 className="size-4" />
                  {preview.data?.row_count ??
                    readMetric(selected.metadata, 'records') ??
                    'n/a'}{' '}
                  records
                </div>
                <div>
                  <Columns3 className="size-4" />
                  {preview.data?.columns.length ||
                    readMetric(selected.metadata, 'schema') ||
                    selected.schema_name ||
                    'n/a'}{' '}
                  columns
                </div>
              </div>
              <div
                className="phlo-v2-tab-row"
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
                preview={preview.data}
                selected={selected}
                setSql={setSql}
                sql={sql}
              />
              {preview.error && (
                <div className="phlo-v2-panel-footer">{preview.error}</div>
              )}
            </>
          ) : (
            <p>No table selected.</p>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
  )
}

type DataDetailTab = 'preview' | 'sql' | 'journey'

const dataDetailTabs: Array<{
  id: DataDetailTab
  label: string
  icon: ReactNode
}> = [
  { id: 'preview', label: 'Preview', icon: <Rows3 className="size-3.5" /> },
  { id: 'sql', label: 'SQL', icon: <Terminal className="size-3.5" /> },
  { id: 'journey', label: 'Journey', icon: <GitBranch className="size-3.5" /> },
]

function DataDetailPanel({
  active,
  preview,
  selected,
  setSql,
  sql,
}: {
  active: DataDetailTab
  preview: V2TablePreview | null
  selected: V2Table
  setSql: (value: string) => void
  sql: string
}) {
  if (active === 'sql') {
    return (
      <div className="phlo-v2-query-panel">
        <div className="phlo-v2-workspace-toolbar">
          <span>SQL</span>
          <span className="phlo-v2-pill">read only</span>
        </div>
        <textarea
          onChange={(event) => setSql(event.target.value)}
          value={selected ? sql.replace('selected_table', selected.name) : sql}
        />
        <div className="phlo-v2-action-row">
          <button
            disabled
            title="Query execution requires a v2 phlo-api query contract."
            type="button"
          >
            <Play className="size-3.5" />
            Run
          </button>
          <button
            disabled
            title="Saved queries require a v2 phlo-api persistence contract."
            type="button"
          >
            <Save className="size-3.5" />
            Save
          </button>
        </div>
      </div>
    )
  }

  if (active === 'journey') {
    return (
      <div className="phlo-v2-detail-list">
        <div className="phlo-v2-mini-row">
          <span>Asset binding</span>
          <small>{selected.asset_id ?? 'none'}</small>
        </div>
        <div className="phlo-v2-mini-row">
          <span>Row journey</span>
          <small>
            Waiting for provider-neutral row identity in phlo-api v2
          </small>
        </div>
        <div className="phlo-v2-mini-row">
          <span>Branch</span>
          <small>{selected.branch ?? 'main'}</small>
        </div>
      </div>
    )
  }

  return (
    <div className="phlo-v2-detail-list">
      {(preview?.columns ?? []).slice(0, 6).map((column) => (
        <div className="phlo-v2-mini-row" key={column}>
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

function buildTableGraph(tables: Array<V2Table>): {
  nodes: Array<V2FlowNode>
  edges: Array<V2FlowEdge>
} {
  const namespaceNodes = Array.from(
    new Set(tables.map((table) => table.namespace ?? 'default')),
  ).map(
    (namespace): V2FlowNode => ({
      id: `namespace:${namespace}`,
      label: namespace,
      kind: 'branch',
      lane: 'branch',
      subtitle: 'namespace',
    }),
  )

  const tableNodes = tables.map(
    (table): V2FlowNode => ({
      id: table.id,
      label: table.name,
      kind: 'table',
      lane: 'table',
      subtitle: table.asset_id ?? table.schema_name,
      metric: `${table.format ?? 'unknown'} · ${readMetric(table.metadata, 'records') ?? 'n/a'} rows`,
    }),
  )

  const edges = tables.map(
    (table): V2FlowEdge => ({
      id: `namespace:${table.namespace ?? 'default'}->${table.id}`,
      source: `namespace:${table.namespace ?? 'default'}`,
      target: table.id,
    }),
  )

  return { nodes: [...namespaceNodes, ...tableNodes], edges }
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

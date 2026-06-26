import { createFileRoute } from '@tanstack/react-router'
import {
  Activity,
  Database,
  GitBranch,
  Network,
  Search,
  ShieldCheck,
  Table2,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryAsset,
  ObservatoryLogEvent,
  ObservatoryOperation,
  ObservatoryQualityCheck,
  ObservatoryTable,
  ObservatoryTablePreview,
} from '@/observatory/api/types'
import type { ObservatoryFlowEdge, ObservatoryFlowNode } from '@/observatory/components/ObservatoryFlowCanvas'
import {
  getObservatoryAssetRecords,
  getObservatoryLogRecords,
  getObservatoryOperationRecords,
  getObservatoryQualityRecords,
  getObservatoryTablePreview,
  getObservatoryTableRecords,
} from '@/observatory/api/resources'
import { ObservatoryFlowCanvas } from '@/observatory/components/ObservatoryFlowCanvas'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { readMetric, useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/assets')({
  component: Assets,
})

export function Assets() {
  const result = useLiveResource(getObservatoryAssetRecords, 120_000, 'v2:assets')
  const tablesResult = useLiveResource(getObservatoryTableRecords, 120_000, 'v2:tables')
  const qualityResult = useLiveResource(
    getObservatoryQualityRecords,
    120_000,
    'v2:quality',
  )
  const logsResult = useLiveResource(getObservatoryLogRecords, 120_000, 'v2:logs')
  const operationsResult = useLiveResource(
    getObservatoryOperationRecords,
    120_000,
    'v2:operations',
  )
  const assets = result.data ?? []
  const tables = tablesResult.data ?? []
  const quality = qualityResult.data ?? []
  const logs = logsResult.data ?? []
  const operations = operationsResult.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeDetail, setActiveDetail] = useState<AssetDetailTab>('overview')
  const [query, setQuery] = useState('')
  const downstreamCounts = useMemo(
    () => buildDownstreamCounts(assets),
    [assets],
  )
  const filteredAssets = useMemo(
    () =>
      filterAssets(assets, query).sort(
        (left, right) =>
          assetScore(right, downstreamCounts) -
          assetScore(left, downstreamCounts),
      ),
    [assets, downstreamCounts, query],
  )
  const selected =
    assets.find((asset) => asset.id === selectedId) ??
    chooseDefaultAsset(filteredAssets.length ? filteredAssets : assets, assets)
  const graph = useMemo(
    () => buildAssetNeighborhood(assets, selected?.id ?? null),
    [assets, selected?.id],
  )
  const qualityChecks = assets.reduce(
    (sum, asset) => sum + asset.checks.length,
    0,
  )
  const dependencies = assets.reduce(
    (sum, asset) => sum + asset.dependencies.length,
    0,
  )
  const groups = new Set(assets.map((asset) => asset.group ?? 'ungrouped')).size
  const detail = selected
    ? buildAssetDetail(selected, assets, tables, quality, logs, operations)
    : null
  const primaryTable = detail?.tables[0] ?? null
  const [preview, setPreview] = useState<{
    tableId: string | null
    data: ObservatoryTablePreview | null
    error: string | null
  }>({ tableId: null, data: null, error: null })

  useEffect(() => {
    if (!primaryTable) {
      setPreview({ tableId: null, data: null, error: null })
      return
    }

    let cancelled = false
    getObservatoryTablePreview({ data: { tableId: primaryTable.id, limit: 5 } }).then(
      (response) => {
        if (cancelled) return
        setPreview({
          tableId: primaryTable.id,
          data: response.data,
          error: response.error,
        })
      },
    )

    return () => {
      cancelled = true
    }
  }, [primaryTable?.id])

  const selectedPreview =
    preview.tableId === primaryTable?.id ? preview.data : null
  const selectedPreviewError =
    preview.tableId === primaryTable?.id ? preview.error : null
  const selectedTableStats = primaryTable
    ? tableStats(primaryTable, selectedPreview, selectedPreviewError)
    : null

  return (
    <ObservatoryPage
      kicker="Assets"
      title="Impact browser"
      description="Find an asset, inspect its blast radius, then follow the table, issue, and activity evidence around it."
      action={<span className="phlo-observatory-pill">{assets.length} assets</span>}
    >
      <section className="phlo-observatory-diff-metrics">
        <Metric
          icon={<Database className="size-5" />}
          label="Registered Assets"
          value={assets.length}
        />
        <Metric
          icon={<Network className="size-5" />}
          label="Dependencies"
          value={dependencies}
        />
        <Metric
          icon={<ShieldCheck className="size-5" />}
          label="Quality Checks"
          value={qualityChecks}
        />
        <Metric
          icon={<GitBranch className="size-5" />}
          label="Groups"
          value={groups}
        />
      </section>

      <section className="phlo-observatory-assets-workbench">
        <div className="phlo-observatory-asset-index">
          <div className="phlo-observatory-index-toolbar">
            <h2>Asset Index</h2>
            <label className="phlo-observatory-search-field">
              <Search className="size-4" />
              <input
                aria-label="Search assets"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search assets, groups, checks"
                value={query}
              />
            </label>
          </div>
          <div className="phlo-observatory-asset-table" role="table">
            <div className="phlo-observatory-asset-table-head" role="row">
              <span>Name</span>
              <span>Checks</span>
              <span>Impact</span>
            </div>
            {filteredAssets.map((asset) => (
              <button
                className="phlo-observatory-asset-table-row"
                data-active={asset.id === selected?.id}
                key={asset.id}
                onClick={() => setSelectedId(asset.id)}
                role="row"
                type="button"
              >
                <span>{asset.name}</span>
                <span>{asset.checks.length}</span>
                <span>{downstreamCounts.get(asset.id) ?? 0}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="phlo-observatory-asset-flow">
          <div className="phlo-observatory-workspace-toolbar">
            <span>
              <Network className="size-4" />
              Neighborhood
            </span>
            <span className="phlo-observatory-pill">{graph.edges.length} links</span>
          </div>
          <ObservatoryFlowCanvas
            edges={graph.edges}
            nodes={graph.nodes}
            onSelect={setSelectedId}
            selectedId={selected?.id}
          />
        </div>

        <aside className="phlo-observatory-asset-detail">
          {selected ? (
            <>
              <div className="phlo-observatory-detail-header">
                <span>{selected.group ?? 'asset'}</span>
                <h2>{selected.name}</h2>
                <p>{summarizeDescription(selected.description)}</p>
              </div>
              <dl className="phlo-observatory-facts">
                <Fact
                  label="Downstream"
                  value={downstreamCounts.get(selected.id) ?? 0}
                />
                <Fact
                  label="Records"
                  value={
                    selectedTableStats?.records ??
                    readMetric(selected.metadata, 'records')
                  }
                />
                <Fact
                  label="Columns"
                  value={
                    selectedTableStats?.columns ??
                    readMetric(selected.metadata, 'columns')
                  }
                />
                <Fact
                  label="Format"
                  value={
                    selectedTableStats?.format ??
                    readMetric(selected.metadata, 'format')
                  }
                />
                <Fact
                  label="Namespace"
                  value={
                    selectedTableStats?.namespace ??
                    readMetric(selected.metadata, 'namespace')
                  }
                />
              </dl>
              <div className="phlo-observatory-chip-cloud">
                {selected.dependencies.map((dependency) => (
                  <span className="phlo-observatory-chip" key={dependency}>
                    <GitBranch className="size-3" />
                    {dependency}
                  </span>
                ))}
                {selected.checks.map((check) => (
                  <span className="phlo-observatory-chip" key={check}>
                    <ShieldCheck className="size-3" />
                    {check}
                  </span>
                ))}
              </div>
              <div
                className="phlo-observatory-tab-row"
                role="tablist"
                aria-label="Asset detail"
              >
                {assetDetailTabs.map((tab) => (
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
              {detail && (
                <AssetDetailPanel
                  active={activeDetail}
                  detail={detail}
                  preview={selectedPreview}
                  selected={selected}
                />
              )}
            </>
          ) : (
            <p>No assets registered yet.</p>
          )}
          {result.error && (
            <div className="phlo-observatory-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </ObservatoryPage>
  )
}

type AssetDetailTab = 'overview' | 'tables' | 'quality' | 'activity'

const assetDetailTabs: Array<{
  id: AssetDetailTab
  label: string
  icon: ReactNode
}> = [
  { id: 'overview', label: 'Overview', icon: <Network className="size-3.5" /> },
  { id: 'tables', label: 'Tables', icon: <Table2 className="size-3.5" /> },
  {
    id: 'quality',
    label: 'Quality',
    icon: <ShieldCheck className="size-3.5" />,
  },
  {
    id: 'activity',
    label: 'Activity',
    icon: <Activity className="size-3.5" />,
  },
]

interface AssetDetailModel {
  upstream: Array<ObservatoryAsset>
  downstream: Array<ObservatoryAsset>
  tables: Array<ObservatoryTable>
  quality: Array<ObservatoryQualityCheck>
  logs: Array<ObservatoryLogEvent>
  operations: Array<ObservatoryOperation>
}

function AssetDetailPanel({
  active,
  detail,
  preview,
  selected,
}: {
  active: AssetDetailTab
  detail: AssetDetailModel
  preview: ObservatoryTablePreview | null
  selected: ObservatoryAsset
}) {
  if (active === 'tables') {
    return (
      <div className="phlo-observatory-detail-list">
        {detail.tables.length ? (
          detail.tables.map((table) => (
            <div className="phlo-observatory-mini-row" key={table.id}>
              <span>
                {table.namespace
                  ? `${table.namespace}.${table.name}`
                  : table.name}
              </span>
              <small>
                {table.id === preview?.table.id
                  ? [
                      table.format,
                      preview.row_count === null ||
                      preview.row_count === undefined
                        ? null
                        : `${preview.row_count} records`,
                      `${preview.columns.length} columns`,
                    ]
                      .filter(Boolean)
                      .join(' · ')
                  : [table.format, table.branch].filter(Boolean).join(' · ') ||
                    'table'}
              </small>
            </div>
          ))
        ) : (
          <p>No tables linked to this asset yet.</p>
        )}
      </div>
    )
  }

  if (active === 'quality') {
    return (
      <div className="phlo-observatory-detail-list">
        {detail.quality.length ? (
          detail.quality.map((check) => (
            <div className="phlo-observatory-mini-row" key={check.id}>
              <span>{check.name}</span>
              <small>
                {[check.status, check.severity].filter(Boolean).join(' · ')}
              </small>
            </div>
          ))
        ) : (
          <p>No quality checks linked to this asset yet.</p>
        )}
      </div>
    )
  }

  if (active === 'activity') {
    const activity = [
      ...detail.operations.map((operation) => ({
        id: `operation:${operation.id}`,
        label: operation.name,
        meta: [operation.kind, operation.status].filter(Boolean).join(' · '),
      })),
      ...detail.logs.map((log) => ({
        id: `log:${log.id}`,
        label: log.message,
        meta: [log.level, log.source].filter(Boolean).join(' · '),
      })),
    ]
    return (
      <div className="phlo-observatory-detail-list">
        {activity.length ? (
          activity.map((item) => (
            <div className="phlo-observatory-mini-row" key={item.id}>
              <span>{item.label}</span>
              <small>{item.meta}</small>
            </div>
          ))
        ) : (
          <p>No activity linked to this asset yet.</p>
        )}
      </div>
    )
  }

  return (
    <div className="phlo-observatory-detail-list">
      <div className="phlo-observatory-mini-row">
        <span>Upstream</span>
        <small>
          {detail.upstream.map((asset) => asset.name).join(', ') || 'none'}
        </small>
      </div>
      <div className="phlo-observatory-mini-row">
        <span>Downstream</span>
        <small>
          {detail.downstream.map((asset) => asset.name).join(', ') || 'none'}
        </small>
      </div>
      <div className="phlo-observatory-mini-row">
        <span>Resources</span>
        <small>{selected.resources.join(', ') || 'none'}</small>
      </div>
    </div>
  )
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: number
}) {
  return (
    <div className="phlo-observatory-diff-metric">
      {icon}
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

function buildAssetDetail(
  selected: ObservatoryAsset,
  assets: Array<ObservatoryAsset>,
  tables: Array<ObservatoryTable>,
  quality: Array<ObservatoryQualityCheck>,
  logs: Array<ObservatoryLogEvent>,
  operations: Array<ObservatoryOperation>,
): AssetDetailModel {
  return {
    upstream: assets.filter((asset) =>
      selected.dependencies.includes(asset.id),
    ),
    downstream: assets.filter((asset) =>
      asset.dependencies.includes(selected.id),
    ),
    tables: tables.filter((table) => table.asset_id === selected.id),
    quality: quality.filter((check) => check.asset_id === selected.id),
    logs: logs.filter(
      (log) =>
        log.resource?.kind === 'asset' && log.resource.id === selected.id,
    ),
    operations: operations.filter(
      (operation) =>
        operation.target?.id === selected.id &&
        (operation.target.kind === 'asset' ||
          operation.target.kind === 'table'),
    ),
  }
}

function filterAssets(assets: Array<ObservatoryAsset>, query: string): Array<ObservatoryAsset> {
  const needle = query.trim().toLowerCase()
  if (!needle) return assets
  return assets.filter((asset) =>
    [
      asset.name,
      asset.group,
      asset.description,
      ...asset.checks,
      ...asset.dependencies,
    ]
      .filter(Boolean)
      .some((value) => value!.toLowerCase().includes(needle)),
  )
}

function chooseDefaultAsset(
  candidates: Array<ObservatoryAsset>,
  assets: Array<ObservatoryAsset>,
): ObservatoryAsset | null {
  if (!candidates.length) return null
  const downstreamCounts = buildDownstreamCounts(assets)
  let best = candidates[0]
  let bestScore = assetScore(best, downstreamCounts)
  for (const candidate of candidates.slice(1)) {
    const score = assetScore(candidate, downstreamCounts)
    if (score > bestScore) {
      best = candidate
      bestScore = score
    }
  }
  return best
}

function buildDownstreamCounts(assets: Array<ObservatoryAsset>): Map<string, number> {
  const downstreamCounts = new Map<string, number>()
  assets.forEach((asset) => {
    asset.dependencies.forEach((dependency) => {
      downstreamCounts.set(
        dependency,
        (downstreamCounts.get(dependency) ?? 0) + 1,
      )
    })
  })
  return downstreamCounts
}

function assetScore(
  asset: ObservatoryAsset,
  downstreamCounts: Map<string, number>,
): number {
  return (
    asset.dependencies.length * 2 +
    (downstreamCounts.get(asset.id) ?? 0) * 3 +
    asset.checks.length
  )
}

function buildAssetNeighborhood(
  assets: Array<ObservatoryAsset>,
  selectedId: string | null,
): {
  nodes: Array<ObservatoryFlowNode>
  edges: Array<ObservatoryFlowEdge>
} {
  const assetById = new Map(assets.map((asset) => [asset.id, asset]))
  const selected = selectedId ? assetById.get(selectedId) : assets[0]
  if (!selected) return { nodes: [], edges: [] }

  const relatedIds = new Set<string>([selected.id])
  selected.dependencies.forEach((dependency) => relatedIds.add(dependency))
  for (const asset of assets) {
    for (const dependency of asset.dependencies) {
      if (dependency === selected.id) {
        relatedIds.add(asset.id)
        break
      }
    }
  }

  const neighborhood = assets.filter((asset) => relatedIds.has(asset.id))
  const nodes = neighborhood.map(
    (asset): ObservatoryFlowNode => ({
      id: asset.id,
      label: asset.name,
      kind: 'asset',
      lane: assetLane(asset),
      subtitle: asset.description,
      metric: `${asset.checks.length} checks`,
    }),
  )
  const edges = neighborhood.flatMap((asset) => {
    const assetEdges: Array<ObservatoryFlowEdge> = []
    for (const dependency of asset.dependencies) {
      if (!relatedIds.has(dependency)) continue
      assetEdges.push({
        id: `${dependency}->${asset.id}`,
        source: dependency,
        target: asset.id,
      })
    }
    return assetEdges
  })

  return { nodes, edges }
}

function assetLane(asset: ObservatoryAsset): string {
  const group = (asset.group ?? '').toLowerCase()
  const name = asset.name.toLowerCase()
  if (group === 'nightscout' || name.startsWith('dlt_')) return 'raw'
  if (group === 'bronze' || name.startsWith('stg_')) return 'bronze'
  if (group === 'silver') return 'silver'
  if (group === 'gold') return 'gold'
  if (group === 'marts' || name.startsWith('mrt_')) return 'marts'
  return 'other'
}

function summarizeDescription(description?: string | null): string {
  if (!description) return 'No description returned.'
  const compact = description.replace(/\s+/g, ' ').trim()
  return compact.length > 220 ? `${compact.slice(0, 217)}...` : compact
}

function Fact({
  label,
  value,
}: {
  label: string
  value: string | number | boolean | null | undefined
}) {
  return (
    <>
      <dt>{label}</dt>
      <dd>
        {value === null || value === undefined || value === ''
          ? 'pending'
          : String(value)}
      </dd>
    </>
  )
}

function tableStats(
  table: ObservatoryTable,
  preview: ObservatoryTablePreview | null,
  error: string | null,
): {
  records: string | number
  columns: string | number
  format: string
  namespace: string
} {
  const records =
    preview?.row_count ??
    readMetric(table.metadata, 'records') ??
    readMetric(table.metadata, 'row_count') ??
    (error ? 'unavailable' : 'profiling')
  const columns =
    preview?.columns.length ??
    readMetric(table.metadata, 'columns') ??
    (error ? 'unavailable' : 'profiling')

  return {
    records,
    columns,
    format: table.format ?? 'table',
    namespace: table.namespace ?? table.schema_name ?? 'default',
  }
}

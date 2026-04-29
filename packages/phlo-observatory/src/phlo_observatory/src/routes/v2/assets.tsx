import { createFileRoute } from '@tanstack/react-router'
import {
  Activity,
  Database,
  GitBranch,
  Network,
  Search,
  ShieldCheck,
  Table2,
  Terminal,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2Asset,
  V2LogEvent,
  V2Operation,
  V2QualityCheck,
  V2Table,
} from '@/v2/api/types'
import type { V2FlowEdge, V2FlowNode } from '@/v2/components/V2FlowCanvas'
import {
  getV2AssetRecords,
  getV2LogRecords,
  getV2OperationRecords,
  getV2QualityRecords,
  getV2TableRecords,
} from '@/v2/api/resources'
import { V2FlowCanvas } from '@/v2/components/V2FlowCanvas'
import { V2Page } from '@/v2/components/V2Page'
import { readMetric, useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/assets')({
  component: Assets,
})

function Assets() {
  const result = useLiveResource(getV2AssetRecords)
  const tablesResult = useLiveResource(getV2TableRecords)
  const qualityResult = useLiveResource(getV2QualityRecords)
  const logsResult = useLiveResource(getV2LogRecords)
  const operationsResult = useLiveResource(getV2OperationRecords)
  const assets = result.data ?? []
  const tables = tablesResult.data ?? []
  const quality = qualityResult.data ?? []
  const logs = logsResult.data ?? []
  const operations = operationsResult.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeDetail, setActiveDetail] = useState<AssetDetailTab>('overview')
  const [query, setQuery] = useState('')
  const filteredAssets = useMemo(
    () => filterAssets(assets, query),
    [assets, query],
  )
  const selected =
    assets.find((asset) => asset.id === selectedId) ??
    filteredAssets[0] ??
    assets[0] ??
    null
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

  return (
    <V2Page
      kicker="Assets"
      title="Assets"
      description="Search, inspect, and trace the lakehouse asset graph."
      action={<span className="phlo-v2-pill">{assets.length} assets</span>}
    >
      <section className="phlo-v2-diff-metrics">
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

      <section className="phlo-v2-assets-workbench">
        <div className="phlo-v2-asset-index">
          <div className="phlo-v2-index-toolbar">
            <h2>Asset Index</h2>
            <label className="phlo-v2-search-field">
              <Search className="size-4" />
              <input
                aria-label="Search assets"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search assets, groups, checks"
                value={query}
              />
            </label>
          </div>
          <div className="phlo-v2-asset-table" role="table">
            <div className="phlo-v2-asset-table-head" role="row">
              <span>Name</span>
              <span>Checks</span>
              <span>Deps</span>
            </div>
            {filteredAssets.map((asset) => (
              <button
                className="phlo-v2-asset-table-row"
                data-active={asset.id === selected?.id}
                key={asset.id}
                onClick={() => setSelectedId(asset.id)}
                role="row"
                type="button"
              >
                <span>{asset.name}</span>
                <span>{asset.checks.length}</span>
                <span>{asset.dependencies.length}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="phlo-v2-asset-flow">
          <div className="phlo-v2-workspace-toolbar">
            <span>
              <Network className="size-4" />
              Neighborhood
            </span>
            <span className="phlo-v2-pill">{graph.edges.length} links</span>
          </div>
          <V2FlowCanvas
            edges={graph.edges}
            nodes={graph.nodes}
            onSelect={setSelectedId}
            selectedId={selected?.id}
          />
        </div>

        <aside className="phlo-v2-asset-detail">
          {selected ? (
            <>
              <div className="phlo-v2-detail-header">
                <span>{selected.group ?? 'asset'}</span>
                <h2>{selected.name}</h2>
                <p>{selected.description ?? 'No description returned.'}</p>
              </div>
              <dl className="phlo-v2-facts">
                <Fact
                  label="Freshness"
                  value={readMetric(selected.metadata, 'freshness')}
                />
                <Fact
                  label="Records"
                  value={readMetric(selected.metadata, 'records')}
                />
                <Fact
                  label="Format"
                  value={readMetric(selected.metadata, 'format')}
                />
                <Fact
                  label="Branch"
                  value={readMetric(selected.metadata, 'branch')}
                />
              </dl>
              <div className="phlo-v2-chip-cloud">
                {selected.dependencies.map((dependency) => (
                  <span className="phlo-v2-chip" key={dependency}>
                    <GitBranch className="size-3" />
                    {dependency}
                  </span>
                ))}
                {selected.checks.map((check) => (
                  <span className="phlo-v2-chip" key={check}>
                    <ShieldCheck className="size-3" />
                    {check}
                  </span>
                ))}
              </div>
              <div
                className="phlo-v2-tab-row"
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
                  selected={selected}
                />
              )}
            </>
          ) : (
            <p>No assets registered by phlo-api v2.</p>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
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
  upstream: Array<V2Asset>
  downstream: Array<V2Asset>
  tables: Array<V2Table>
  quality: Array<V2QualityCheck>
  logs: Array<V2LogEvent>
  operations: Array<V2Operation>
}

function AssetDetailPanel({
  active,
  detail,
  selected,
}: {
  active: AssetDetailTab
  detail: AssetDetailModel
  selected: V2Asset
}) {
  if (active === 'tables') {
    return (
      <div className="phlo-v2-detail-list">
        {detail.tables.length ? (
          detail.tables.map((table) => (
            <div className="phlo-v2-mini-row" key={table.id}>
              <span>
                {table.namespace
                  ? `${table.namespace}.${table.name}`
                  : table.name}
              </span>
              <small>
                {[table.format, table.branch].filter(Boolean).join(' · ') ||
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
      <div className="phlo-v2-detail-list">
        {detail.quality.length ? (
          detail.quality.map((check) => (
            <div className="phlo-v2-mini-row" key={check.id}>
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
      <div className="phlo-v2-detail-list">
        {activity.length ? (
          activity.map((item) => (
            <div className="phlo-v2-mini-row" key={item.id}>
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
    <div className="phlo-v2-detail-list">
      <div className="phlo-v2-mini-row">
        <span>Upstream</span>
        <small>
          {detail.upstream.map((asset) => asset.name).join(', ') || 'none'}
        </small>
      </div>
      <div className="phlo-v2-mini-row">
        <span>Downstream</span>
        <small>
          {detail.downstream.map((asset) => asset.name).join(', ') || 'none'}
        </small>
      </div>
      <div className="phlo-v2-mini-row">
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
    <div className="phlo-v2-diff-metric">
      {icon}
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

function buildAssetDetail(
  selected: V2Asset,
  assets: Array<V2Asset>,
  tables: Array<V2Table>,
  quality: Array<V2QualityCheck>,
  logs: Array<V2LogEvent>,
  operations: Array<V2Operation>,
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

function filterAssets(assets: Array<V2Asset>, query: string): Array<V2Asset> {
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

function buildAssetNeighborhood(
  assets: Array<V2Asset>,
  selectedId: string | null,
): {
  nodes: Array<V2FlowNode>
  edges: Array<V2FlowEdge>
} {
  const assetById = new Map(assets.map((asset) => [asset.id, asset]))
  const selected = selectedId ? assetById.get(selectedId) : assets[0]
  if (!selected) return { nodes: [], edges: [] }

  const relatedIds = new Set<string>([selected.id])
  selected.dependencies.forEach((dependency) => relatedIds.add(dependency))
  assets
    .filter((asset) => asset.dependencies.includes(selected.id))
    .forEach((asset) => relatedIds.add(asset.id))

  const neighborhood = assets.filter((asset) => relatedIds.has(asset.id))
  const nodes = neighborhood.map(
    (asset): V2FlowNode => ({
      id: asset.id,
      label: asset.name,
      kind: 'asset',
      lane: asset.group ?? 'other',
      subtitle: asset.description,
      metric: `${asset.checks.length} checks`,
    }),
  )
  const edges = neighborhood.flatMap((asset) =>
    asset.dependencies
      .filter((dependency) => relatedIds.has(dependency))
      .map((dependency) => ({
        id: `${dependency}->${asset.id}`,
        source: dependency,
        target: asset.id,
      })),
  )

  return { nodes, edges }
}

function Fact({
  label,
  value,
}: {
  label: string
  value: string | number | boolean | null
}) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value === null ? 'n/a' : String(value)}</dd>
    </>
  )
}

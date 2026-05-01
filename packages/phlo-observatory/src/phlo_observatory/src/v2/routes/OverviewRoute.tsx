import {
  Activity,
  AlertCircle,
  Boxes,
  Database,
  GitBranch,
  ListChecks,
  Server,
} from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2Asset,
  V2Branch,
  V2Capabilities,
  V2LogEvent,
  V2Operation,
  V2Overview,
  V2QualityCheck,
  V2ResourceResult,
  V2Service,
} from '@/v2/api/types'
import {
  getV2AssetRecords,
  getV2Branches,
  getV2Capabilities,
  getV2LogRecords,
  getV2OperationRecords,
  getV2Overview,
  getV2QualityRecords,
  getV2Services,
} from '@/v2/api/resources'
import { StatusBadge } from '@/v2/components/StatusBadge'
import { loadCachedResource } from '@/v2/routes/liveResource'

const formatter = new Intl.NumberFormat('en')

export function OverviewRoute() {
  const [overview, setOverview] = useState<V2ResourceResult<V2Overview>>({
    data: null,
    error: null,
  })
  const [services, setServices] = useState<V2ResourceResult<Array<V2Service>>>({
    data: null,
    error: null,
  })
  const [operations, setOperations] = useState<
    V2ResourceResult<Array<V2Operation>>
  >({
    data: null,
    error: null,
  })
  const [assets, setAssets] = useState<V2ResourceResult<Array<V2Asset>>>({
    data: null,
    error: null,
  })
  const [quality, setQuality] = useState<
    V2ResourceResult<Array<V2QualityCheck>>
  >({
    data: null,
    error: null,
  })
  const [logs, setLogs] = useState<V2ResourceResult<Array<V2LogEvent>>>({
    data: null,
    error: null,
  })
  const [branches, setBranches] = useState<V2ResourceResult<Array<V2Branch>>>({
    data: null,
    error: null,
  })
  const [capabilities, setCapabilities] =
    useState<V2ResourceResult<V2Capabilities> | null>(null)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      const nextCapabilities = await loadCachedResource(
        'v2:capabilities',
        getV2Capabilities,
        {
          staleMs: 120_000,
        },
      )
      const features = nextCapabilities.data?.features
      const empty = { data: [], error: null }
      const [
        nextOverview,
        nextServices,
        nextOperations,
        nextAssets,
        nextQuality,
        nextLogs,
        nextBranches,
      ] = await Promise.all([
        loadCachedResource('v2:overview', getV2Overview, { staleMs: 30_000 }),
        loadCachedResource('v2:services', getV2Services, { staleMs: 60_000 }),
        features?.operations === false
          ? empty
          : loadCachedResource('v2:operations', getV2OperationRecords, {
              staleMs: 60_000,
            }),
        features?.assets === false
          ? empty
          : loadCachedResource('v2:assets', getV2AssetRecords, {
              staleMs: 60_000,
            }),
        features?.issues === false
          ? empty
          : loadCachedResource('v2:quality', getV2QualityRecords, {
              staleMs: 60_000,
            }),
        features?.logs === false
          ? empty
          : loadCachedResource('v2:logs', getV2LogRecords, { staleMs: 30_000 }),
        features?.branches === false
          ? empty
          : loadCachedResource('v2:branches', getV2Branches, {
              staleMs: 60_000,
            }),
      ])

      if (!cancelled) {
        setOverview(nextOverview)
        setServices(nextServices)
        setOperations(nextOperations)
        setAssets(nextAssets)
        setQuality(nextQuality)
        setLogs(nextLogs)
        setBranches(nextBranches)
        setCapabilities(nextCapabilities)
        setUpdatedAt(new Date())
      }
    }

    void load()
    const interval = window.setInterval(load, 30_000)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  const serviceRows = services.data ?? []
  const operationRows = operations.data ?? []
  const assetRows = assets.data ?? []
  const qualityRows = quality.data ?? []
  const logRows = logs.data ?? []
  const branchRows = branches.data ?? []
  const counters = overview.data?.counters ?? {}
  const runningServices = useMemo(
    () => serviceRows.filter((service) => service.status === 'running').length,
    [serviceRows],
  )
  const attentionServices = useMemo(
    () => serviceRows.filter(serviceNeedsAttention).length,
    [serviceRows],
  )
  const blockingChecks = qualityRows.filter((check) => check.blocking).length
  const failedOperations = operationRows.filter(
    (operation) => operation.status === 'failed',
  ).length
  const activeBranches = branchRows.filter((branch) => !branch.current).length
  const errorLogs = logRows.filter((log) => log.level === 'error').length
  const attentionItems = buildAttentionItems({
    services: serviceRows,
    operations: operationRows,
    quality: qualityRows,
    logs: logRows,
    enabled: capabilities?.data?.features,
  })
  const recentEvidence = logRows.slice(0, 4)
  const apiError =
    overview.error ??
    services.error ??
    operations.error ??
    assets.error ??
    quality.error ??
    logs.error ??
    branches.error

  return (
    <div className="phlo-v2-content">
      <header className="phlo-v2-section-header">
        <div>
          <div className="phlo-v2-kicker">Overview</div>
          <h1 className="phlo-v2-title">Lakehouse control</h1>
          <p className="phlo-v2-subtitle">
            The cross-domain queue: what needs attention, why it matters, and
            where to move next.
          </p>
        </div>
        <StatusBadge
          label={overview.data?.health.message ?? 'API pending'}
          state={
            overview.data?.health.state ?? (apiError ? 'warning' : 'unknown')
          }
        />
      </header>

      <section className="phlo-v2-grid" aria-label="Platform counters">
        <MetricTile
          icon={<Server className="size-4" />}
          label="Services"
          note={`${formatter.format(runningServices)} running`}
          value={counterValue(counters.services, serviceRows.length)}
        />
        <MetricTile
          icon={<AlertCircle className="size-4" />}
          label="Attention"
          note="Services, checks, operations, logs"
          value={formatter.format(attentionItems.length)}
        />
        <MetricTile
          icon={<Boxes className="size-4" />}
          label="Assets"
          note="Resources in view"
          value={counterValue(counters.assets, assetRows.length)}
        />
        {featureEnabled(capabilities?.data, 'branches') && (
          <MetricTile
            icon={<GitBranch className="size-4" />}
            label="Change Risk"
            note="Non-current catalog branches"
            value={formatter.format(activeBranches)}
          />
        )}
      </section>

      <section className="phlo-v2-command">
        <div className="phlo-v2-command-primary">
          <div className="phlo-v2-panel">
            <div className="phlo-v2-panel-header">
              <h2 className="phlo-v2-panel-title">Attention queue</h2>
              <span className="phlo-v2-pill">
                <Activity className="size-3.5" />
                {attentionItems.length || 'Clear'}
              </span>
            </div>
            <div className="phlo-v2-list">
              {attentionItems.length > 0 ? (
                attentionItems.map((item) => (
                  <Link className="phlo-v2-row" key={item.id} to={item.href}>
                    <div className="phlo-v2-row-main">
                      <div className="phlo-v2-row-title">
                        <span className="phlo-v2-dot" data-state={item.state} />
                        <span>{item.label}</span>
                      </div>
                      <div className="phlo-v2-row-meta">{item.meta}</div>
                    </div>
                    <span className="phlo-v2-pill">{item.kind}</span>
                  </Link>
                ))
              ) : (
                <EmptyRow label="No active attention items" />
              )}
            </div>
          </div>

          <section className="phlo-v2-diff-metrics">
            {featureEnabled(capabilities?.data, 'issues') && (
              <CommandTile
                href="/v2/quality"
                icon={<ListChecks className="size-5" />}
                label="Triage issues"
                value={`${blockingChecks} blocking`}
              />
            )}
            {featureEnabled(capabilities?.data, 'operations') && (
              <CommandTile
                href="/v2/operations"
                icon={<Activity className="size-5" />}
                label="Review actions"
                value={`${failedOperations} failed`}
              />
            )}
            <CommandTile
              href="/v2/assets"
              icon={<Boxes className="size-5" />}
              label="Inspect impact"
              value={`${assetRows.length} assets`}
            />
            {featureEnabled(capabilities?.data, 'branches') && (
              <CommandTile
                href="/v2/branches"
                icon={<GitBranch className="size-5" />}
                label="Check changes"
                value={`${activeBranches} active`}
              />
            )}
          </section>
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Control context</div>
          <h2>{overview.data?.health.message ?? 'Waiting for API snapshot'}</h2>
          <p>
            Last refreshed{' '}
            {updatedAt ? updatedAt.toLocaleTimeString() : 'after first load'}.
          </p>
          <dl className="phlo-v2-facts">
            <Fact
              label="Services needing attention"
              value={attentionServices}
            />
            <Fact label="Blocking checks" value={blockingChecks} />
            <Fact label="Failed operations" value={failedOperations} />
            <Fact label="Error logs" value={errorLogs} />
          </dl>
          <div className="phlo-v2-detail-list">
            {recentEvidence.length > 0 ? (
              recentEvidence.map((log) => (
                <div className="phlo-v2-mini-row" key={log.id}>
                  <span>{log.message}</span>
                  <small>
                    {[log.level, log.source, log.timestamp]
                      .filter(Boolean)
                      .join(' · ')}
                  </small>
                </div>
              ))
            ) : (
              <div className="phlo-v2-mini-row">
                <span>No recent evidence</span>
                <small>
                  Logs will appear as the API read model reports them.
                </small>
              </div>
            )}
          </div>
          {apiError && <div className="phlo-v2-panel-footer">{apiError}</div>}
        </aside>
      </section>
    </div>
  )
}

function MetricTile({
  icon,
  label,
  note,
  value,
}: {
  icon: ReactNode
  label: string
  note: string
  value: string
}) {
  return (
    <div className="phlo-v2-tile">
      <div className="phlo-v2-tile-label">
        <span>{label}</span>
        {icon}
      </div>
      <div className="phlo-v2-tile-value">{value}</div>
      <div className="phlo-v2-tile-note">{note}</div>
    </div>
  )
}

function CommandTile({
  href,
  icon,
  label,
  value,
}: {
  href: string
  icon: ReactNode
  label: string
  value: string
}) {
  return (
    <Link className="phlo-v2-diff-metric" to={href}>
      {icon}
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </Link>
  )
}

function Fact({ label, value }: { label: string; value: string | number }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{String(value)}</dd>
    </>
  )
}

function EmptyRow({ label }: { label: string }) {
  return (
    <div className="phlo-v2-row">
      <div className="phlo-v2-row-main">
        <div className="phlo-v2-row-title">{label}</div>
        <div className="phlo-v2-row-meta">
          Connect a running lakehouse or add resources to populate this surface.
        </div>
      </div>
    </div>
  )
}

function counterValue(primary?: number, fallback?: number): string {
  const value = primary ?? fallback
  return typeof value === 'number' ? formatter.format(value) : '--'
}

function buildAttentionItems({
  services,
  operations,
  quality,
  logs,
  enabled,
}: {
  services: Array<V2Service>
  operations: Array<V2Operation>
  quality: Array<V2QualityCheck>
  logs: Array<V2LogEvent>
  enabled?: Record<string, boolean>
}) {
  return [
    ...services
      .filter(serviceNeedsAttention)
      .slice(0, 3)
      .map((service) => ({
        id: `service:${service.id}`,
        href: '/v2/services',
        kind: 'service',
        label: service.name,
        meta: service.health.message ?? service.status,
        state: service.health.state,
      })),
    ...(enabled?.issues === false
      ? []
      : quality
          .filter((check) => check.blocking || check.status === 'failing')
          .slice(0, 3)
          .map((check) => ({
            id: `quality:${check.id}`,
            href: '/v2/quality',
            kind: 'quality',
            label: check.name,
            meta: `${check.asset_id} · ${check.severity ?? check.status}`,
            state: check.status === 'failing' ? 'error' : 'warning',
          }))),
    ...(enabled?.operations === false
      ? []
      : operations
          .filter((operation) => operation.status === 'failed')
          .slice(0, 2)
          .map((operation) => ({
            id: `operation:${operation.id}`,
            href: '/v2/operations',
            kind: 'operation',
            label: operation.name,
            meta: operation.target?.label ?? operation.kind,
            state: 'error',
          }))),
    ...(enabled?.logs === false
      ? []
      : logs
          .filter((log) => log.level === 'error')
          .slice(0, 2)
          .map((log) => ({
            id: `log:${log.id}`,
            href: '/v2/logs',
            kind: 'log',
            label: log.message,
            meta: [log.source, log.timestamp].filter(Boolean).join(' · '),
            state: 'error',
          }))),
  ]
}

function featureEnabled(
  capabilities: V2Capabilities | null | undefined,
  key: string,
): boolean {
  if (!capabilities) return true
  return capabilities.features[key] !== false
}

function serviceNeedsAttention(service: V2Service): boolean {
  if (service.health.state === 'error' || service.health.state === 'warning') {
    return true
  }
  if (service.status === 'unhealthy') return true
  return service.status === 'stopped' && service.health.state !== 'ok'
}

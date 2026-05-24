import {
  Activity,
  AlertCircle,
  Boxes,
  Database,
  GitBranch,
  GitCommitHorizontal,
  ListChecks,
  Server,
  Workflow,
} from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { useEffect, useMemo, useReducer } from 'react'
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
  getV2LogRecords,
  getV2OperationRecords,
  getV2Overview,
  getV2QualityRecords,
  getV2Services,
} from '@/v2/api/resources'
import { StatusBadge } from '@/v2/components/StatusBadge'
import {
  loadCachedResource,
  readCachedResource,
} from '@/v2/routes/liveResource'

const formatter = new Intl.NumberFormat('en')
const emptyResult = { data: null, error: null }
const stageTransitions = ['ingest', 'normalize', 'model', 'publish']

type OverviewState = {
  assets: V2ResourceResult<Array<V2Asset>>
  branches: V2ResourceResult<Array<V2Branch>>
  capabilities: V2ResourceResult<V2Capabilities> | null
  logs: V2ResourceResult<Array<V2LogEvent>>
  operations: V2ResourceResult<Array<V2Operation>>
  overview: V2ResourceResult<V2Overview>
  quality: V2ResourceResult<Array<V2QualityCheck>>
  services: V2ResourceResult<Array<V2Service>>
  updatedAt: Date | null
}

export type OverviewSnapshot = Omit<OverviewState, 'updatedAt'> & {
  updatedAt: string | null
}

function overviewReducer(
  state: OverviewState,
  patch: Partial<OverviewState>,
): OverviewState {
  return {
    ...state,
    ...patch,
  }
}

export function loadOverviewSnapshot(): OverviewSnapshot {
  const empty = { data: [], error: null }
  const pending = { data: null, error: null }

  return {
    assets: empty,
    branches: empty,
    capabilities: null,
    logs: empty,
    operations: empty,
    overview: pending,
    quality: empty,
    services: empty,
    updatedAt: null,
  }
}

export async function loadOverviewSnapshotFromApi(): Promise<OverviewSnapshot> {
  const empty = { data: [], error: null }
  const [overview, services, operations, assets, quality, logs] =
    await Promise.all([
      getV2Overview(),
      getV2Services(),
      getV2OperationRecords(),
      getV2AssetRecords(),
      getV2QualityRecords(),
      getV2LogRecords(),
    ])

  return {
    assets,
    branches: empty,
    capabilities: null,
    logs,
    operations,
    overview,
    quality,
    services,
    updatedAt: new Date().toISOString(),
  }
}

export function OverviewRoute({
  initialSnapshot,
}: {
  initialSnapshot?: OverviewSnapshot
}) {
  return useOverviewRoute(initialSnapshot)
}

function useOverviewRoute(initialSnapshot?: OverviewSnapshot) {
  const [
    {
      assets,
      branches,
      capabilities,
      logs,
      operations,
      overview,
      quality,
      services,
      updatedAt,
    },
    setOverviewState,
  ] = useReducer(overviewReducer, {
    assets: initialSnapshot?.assets ?? emptyResult,
    branches: initialSnapshot?.branches ?? emptyResult,
    capabilities: initialSnapshot?.capabilities ?? null,
    logs: initialSnapshot?.logs ?? emptyResult,
    operations: initialSnapshot?.operations ?? emptyResult,
    overview: initialSnapshot?.overview ?? emptyResult,
    quality: initialSnapshot?.quality ?? emptyResult,
    services: initialSnapshot?.services ?? emptyResult,
    updatedAt: initialSnapshot?.updatedAt
      ? new Date(initialSnapshot.updatedAt)
      : null,
  })

  useEffect(() => {
    let cancelled = false

    const cachedSnapshot = readCachedOverviewSnapshot()
    if (cachedSnapshot) {
      setOverviewState({
        ...cachedSnapshot,
        updatedAt: new Date(),
      })
    }

    function load(force = false) {
      const empty = { data: [], error: null }

      loadCachedResource('v2:services', getV2Services, {
        force,
        staleMs: 60_000,
      }).then((nextServices) => {
        if (!cancelled) {
          setOverviewState({ services: nextServices, updatedAt: new Date() })
        }
      })

      loadCachedResource('v2:operations', getV2OperationRecords, {
        force,
        staleMs: 60_000,
      }).then((nextOperations) => {
        if (!cancelled) {
          setOverviewState({
            operations: nextOperations,
            updatedAt: new Date(),
          })
        }
      })

      loadCachedResource('v2:assets', getV2AssetRecords, {
        force,
        staleMs: 60_000,
      }).then((nextAssets) => {
        if (!cancelled) {
          setOverviewState({ assets: nextAssets, updatedAt: new Date() })
        }
      })

      loadCachedResource('v2:quality', getV2QualityRecords, {
        force,
        staleMs: 60_000,
      }).then((nextQuality) => {
        if (!cancelled) {
          setOverviewState({ quality: nextQuality, updatedAt: new Date() })
        }
      })

      loadCachedResource('v2:logs', getV2LogRecords, {
        force,
        staleMs: 30_000,
      }).then((nextLogs) => {
        if (!cancelled) {
          setOverviewState({ logs: nextLogs, updatedAt: new Date() })
        }
      })

      setOverviewState({ branches: empty, capabilities: null })
      loadCachedResource('v2:overview', getV2Overview, {
        force,
        staleMs: 30_000,
      }).then((nextOverview) => {
        if (!cancelled) {
          setOverviewState({ overview: nextOverview, updatedAt: new Date() })
        }
      })
    }

    load(true)
    const interval = window.setInterval(() => {
      load(true)
    }, 30_000)

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
  const hasLakehouseEvidence =
    serviceRows.length > 0 ||
    operationRows.length > 0 ||
    assetRows.length > 0 ||
    qualityRows.length > 0 ||
    logRows.length > 0
  const attentionItems = buildAttentionItems({
    services: serviceRows,
    operations: operationRows,
    quality: qualityRows,
    logs: logRows,
    enabled: capabilities?.data?.features,
  })
  const lakehouseStages = useMemo(
    () => buildLakehouseStages(assetRows, qualityRows),
    [assetRows, qualityRows],
  )
  const eventStory = useMemo(
    () => buildEventStory(operationRows, logRows),
    [logRows, operationRows],
  )
  const integrationLinks = useMemo(
    () => buildIntegrationLinks(serviceRows),
    [serviceRows],
  )
  const recentEvidence = logRows.filter((log) => !isNoisyLog(log)).slice(0, 4)
  const derivedHealth =
    overview.data?.health ??
    (hasLakehouseEvidence
      ? {
          message:
            attentionItems.length > 0
              ? `${attentionItems.length} items need attention`
              : 'Lakehouse snapshot ready',
          state:
            attentionItems.length > 0 ? ('warning' as const) : ('ok' as const),
        }
      : null)
  const apiError =
    services.error ??
    operations.error ??
    assets.error ??
    quality.error ??
    logs.error ??
    branches.error ??
    (hasLakehouseEvidence ? null : overview.error)

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
          label={derivedHealth?.message ?? 'API pending'}
          state={derivedHealth?.state ?? (apiError ? 'warning' : 'unknown')}
        />
      </header>

      <section className="phlo-v2-grid" aria-label="Platform counters">
        <MetricTile
          icon={<Server className="size-4" />}
          label="Services"
          note={`${counterValue(counters.services, serviceRows.length)} tracked`}
          value={formatter.format(runningServices)}
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

      <section className="phlo-v2-lakehouse-map" aria-label="Lakehouse map">
        <div className="phlo-v2-map-header">
          <h2>Lakehouse map</h2>
          <Link className="phlo-v2-map-action" to="/workflows/new">
            <Workflow className="size-4" />
            Build workflow
          </Link>
        </div>
        <div className="phlo-v2-flow-stage-map">
          {lakehouseStages.map((stage, index) => (
            <Link
              className="phlo-v2-stage-card"
              data-state={stage.state}
              data-transition={stageTransitions[index] ?? ''}
              key={stage.id}
              to={stage.href}
            >
              <div className="phlo-v2-stage-card-top">
                <span>{stage.label}</span>
                <StatusBadge label={stage.state} state={stage.state} />
              </div>
              <div className="phlo-v2-stage-body">
                <div className="phlo-v2-stage-primary">
                  <strong>{formatter.format(stage.records)}</strong>
                  <span>records</span>
                </div>
                <small>
                  {stage.assets} assets · {stage.tables} tables ·{' '}
                  {stage.blocking} checks
                </small>
              </div>
              <div className="phlo-v2-stage-samples">
                {stage.samples.length > 0 ? (
                  stage.samples.map((sample) => (
                    <span key={`${stage.id}:${sample}`}>{sample}</span>
                  ))
                ) : (
                  <span>No assets mapped yet</span>
                )}
              </div>
              <div className="phlo-v2-stage-meter">
                <span style={{ width: `${stage.weight}%` }} />
              </div>
            </Link>
          ))}
        </div>
        <div className="phlo-v2-evidence-grid">
          <div className="phlo-v2-evidence-panel">
            <div className="phlo-v2-panel-header">
              <h2 className="phlo-v2-panel-title">Event story</h2>
              <span className="phlo-v2-pill">
                <GitCommitHorizontal className="size-3.5" />
                {eventStory.events.length || 'Empty'}
              </span>
            </div>
            <div className="phlo-v2-timeline">
              {eventStory.events.length > 0 ? (
                eventStory.events.map((event) => (
                  <a
                    className="phlo-v2-timeline-row"
                    data-state={event.state}
                    href={event.href}
                    key={event.id}
                  >
                    <span className="phlo-v2-timeline-dot" />
                    <span>
                      <strong>{event.label}</strong>
                      <small>{event.meta}</small>
                      {event.reason && (
                        <small className="phlo-v2-timeline-reason">
                          {event.reason}
                        </small>
                      )}
                    </span>
                  </a>
                ))
              ) : (
                <EmptyRow label="No events yet" />
              )}
              {eventStory.suppressed > 0 && (
                <div className="phlo-v2-noise-row">
                  {eventStory.suppressed} platform-noise events suppressed
                </div>
              )}
            </div>
          </div>
          <div className="phlo-v2-evidence-panel">
            <div className="phlo-v2-panel-header">
              <h2 className="phlo-v2-panel-title">Native workbenches</h2>
              <span className="phlo-v2-pill">
                <Database className="size-3.5" />
                {integrationLinks.length || 'None'}
              </span>
            </div>
            <div className="phlo-v2-integration-grid">
              {integrationLinks.length > 0 ? (
                integrationLinks.map((link) => (
                  <a
                    className="phlo-v2-integration-link"
                    data-state={link.status}
                    href={link.url}
                    key={`${link.service}:${link.label}:${link.url}`}
                    rel="noreferrer"
                    target="_blank"
                  >
                    <span className="phlo-v2-integration-mark">
                      {link.initials}
                    </span>
                    <span className="phlo-v2-integration-copy">
                      <strong>{link.label}</strong>
                      <span className="phlo-v2-integration-meta">
                        <span>{link.service}</span>
                        <span>{link.description}</span>
                      </span>
                      <code>{link.host}</code>
                    </span>
                    <span className="phlo-v2-integration-status">
                      {link.status}
                    </span>
                  </a>
                ))
              ) : (
                <EmptyRow label="No native links available" />
              )}
            </div>
          </div>
        </div>
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
                  <a className="phlo-v2-row" href={item.href} key={item.id}>
                    <div className="phlo-v2-row-main">
                      <div className="phlo-v2-row-title">
                        <span className="phlo-v2-dot" data-state={item.state} />
                        <span>{item.label}</span>
                      </div>
                      <div className="phlo-v2-row-meta">{item.meta}</div>
                    </div>
                    <span className="phlo-v2-pill">{item.kind}</span>
                  </a>
                ))
              ) : (
                <EmptyRow label="No active attention items" />
              )}
            </div>
          </div>

          <section className="phlo-v2-diff-metrics">
            {(featureEnabled(capabilities?.data, 'issues') ||
              qualityRows.length > 0) && (
              <CommandTile
                href="/quality"
                icon={<ListChecks className="size-5" />}
                label="Triage issues"
                value={`${blockingChecks} blocking`}
              />
            )}
            {featureEnabled(capabilities?.data, 'operations') && (
              <CommandTile
                href="/operations"
                icon={<Activity className="size-5" />}
                label="Review actions"
                value={`${failedOperations} failed`}
              />
            )}
            <CommandTile
              href="/assets"
              icon={<Boxes className="size-5" />}
              label="Inspect impact"
              value={`${assetRows.length} assets`}
            />
            {featureEnabled(capabilities?.data, 'branches') && (
              <CommandTile
                href="/branches"
                icon={<GitBranch className="size-5" />}
                label="Check changes"
                value={`${activeBranches} active`}
              />
            )}
          </section>
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Control context</div>
          <h2>{derivedHealth?.message ?? 'Waiting for API snapshot'}</h2>
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
                  Logs will appear as Phlo and stack services emit events.
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

function readCachedOverviewSnapshot(): Omit<OverviewState, 'updatedAt'> | null {
  const empty = { data: [], error: null }
  const snapshot = {
    assets: readCachedResource<Array<V2Asset>>('v2:assets') ?? empty,
    branches: empty,
    capabilities: null,
    logs: readCachedResource<Array<V2LogEvent>>('v2:logs') ?? empty,
    operations:
      readCachedResource<Array<V2Operation>>('v2:operations') ?? empty,
    overview: readCachedResource<V2Overview>('v2:overview') ?? emptyResult,
    quality: readCachedResource<Array<V2QualityCheck>>('v2:quality') ?? empty,
    services: readCachedResource<Array<V2Service>>('v2:services') ?? empty,
  }

  if (
    (snapshot.assets.data?.length ?? 0) === 0 &&
    (snapshot.operations.data?.length ?? 0) === 0 &&
    (snapshot.services.data?.length ?? 0) === 0 &&
    !snapshot.overview.data
  ) {
    return null
  }

  return snapshot
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

function buildLakehouseStages(
  assets: Array<V2Asset>,
  quality: Array<V2QualityCheck>,
) {
  const stageOrder = ['source', 'bronze', 'silver', 'gold', 'serving']
  const stages = new Map(
    stageOrder.map((stage) => [
      stage,
      {
        id: stage,
        label: stageLabel(stage),
        assets: 0,
        tables: 0,
        records: 0,
        blocking: 0,
        state: 'unknown' as 'ok' | 'warning' | 'error' | 'unknown',
        href: stage === 'serving' ? '/apis' : '/data',
        weight: 8,
        samples: [] as Array<string>,
      },
    ]),
  )
  const qualityByAsset = new Map(
    quality.map((check) => [check.asset_id, check]),
  )

  for (const asset of assets) {
    const stageId = inferStage(asset)
    const stage =
      stages.get(stageId) ??
      stages.get(stageId.replace('analytics', 'gold')) ??
      stages.get('gold')
    if (!stage) continue

    const records = readNumber(asset.metadata.records)
    const tables = asset.kinds.some((kind) =>
      ['table', 'dataset', 'analytics'].includes(kind),
    )
      ? 1
      : 0
    const check = qualityByAsset.get(asset.id)
    stage.assets += 1
    stage.tables += tables
    stage.records += records
    if (check?.blocking) stage.blocking += 1
    if (stage.samples.length < 3) stage.samples.push(asset.name)
    if (check?.status === 'failing') stage.state = 'error'
    else if (check?.status === 'warning' && stage.state !== 'error') {
      stage.state = 'warning'
    } else if (stage.state === 'unknown') {
      stage.state = 'ok'
    }
  }

  const maxRecords = Math.max(
    1,
    ...Array.from(stages.values()).map((stage) => stage.records),
  )
  return Array.from(stages.values()).map((stage) => ({
    ...stage,
    weight: Math.max(8, Math.round((stage.records / maxRecords) * 100)),
  }))
}

function buildEventStory(
  operations: Array<V2Operation>,
  logs: Array<V2LogEvent>,
) {
  const operationEvents = operations.map((operation) => ({
    id: `operation:${operation.id}`,
    href: `/operations?operationId=${encodeURIComponent(operation.id)}`,
    label: operation.name,
    meta: [
      operation.kind,
      operation.target?.label,
      operation.completed_at ?? operation.started_at,
    ]
      .filter(Boolean)
      .join(' · '),
    state: operation.health.state,
    reason:
      operation.status === 'failed' ? failureReason(operation) : undefined,
    sort: operation.completed_at ?? operation.started_at ?? '',
    score: scoreOperation(operation),
  }))
  const noisyLogs = logs.filter(isNoisyLog)
  const logEvents = logs
    .filter((log) => !isNoisyLog(log))
    .map((log) => ({
      id: `log:${log.id}`,
      href: '/logs',
      label: log.message,
      meta: [log.source, log.level, log.timestamp].filter(Boolean).join(' · '),
      reason: undefined,
      state:
        log.level === 'error'
          ? 'error'
          : log.level === 'warning'
            ? 'warning'
            : 'ok',
      sort: log.timestamp ?? '',
      score: scoreLog(log),
    }))
  return {
    events: [...operationEvents, ...logEvents]
      .sort((left, right) => {
        if (left.score !== right.score) return right.score - left.score
        return right.sort.localeCompare(left.sort)
      })
      .slice(0, 6),
    suppressed: noisyLogs.length,
  }
}

function scoreOperation(operation: V2Operation): number {
  let score = 20
  if (operation.kind.startsWith('pipeline.')) score += 50
  if (operation.kind.includes('quality')) score += 35
  if (operation.status === 'failed') score += 45
  if (operation.status === 'succeeded') score += 10
  if (
    operation.target?.kind === 'asset' ||
    operation.target?.kind === 'table'
  ) {
    score += 15
  }
  return score
}

function scoreLog(log: V2LogEvent): number {
  let score = 5
  if (log.level === 'error') score += 40
  if (log.level === 'warning') score += 20
  if (log.resource?.kind === 'asset' || log.resource?.kind === 'table') {
    score += 20
  }
  if (log.source?.toLowerCase().includes('keystone')) score += 20
  return score
}

function isNoisyLog(log: V2LogEvent): boolean {
  const message = log.message.toLowerCase()
  return [
    'unknown_plugin_type',
    'plugin_registry_fetch_fallback',
    'observatory_settings_falling_back_to_memory',
  ].some((needle) => message.includes(needle))
}

function buildIntegrationLinks(services: Array<V2Service>) {
  const browserWorkbenches = new Map<
    string,
    {
      label: string
      path?: string
      preferredPortLabel?: string
      requiresRunning?: boolean
    }
  >([
    ['observatory', { label: 'Observatory', requiresRunning: true }],
    [
      'hasura',
      { label: 'Hasura console', path: '/console', requiresRunning: true },
    ],
    ['phlo-api', { label: 'API docs', path: '/docs', requiresRunning: true }],
    ['dagster', { label: 'Dagster UI', requiresRunning: true }],
    ['grafana', { label: 'Grafana', requiresRunning: true }],
    ['superset', { label: 'Superset', requiresRunning: true }],
    [
      'minio',
      {
        label: 'Object browser',
        preferredPortLabel: ':9001',
        requiresRunning: true,
      },
    ],
    ['pgweb', { label: 'Postgres browser', requiresRunning: true }],
    ['openmetadata', { label: 'OpenMetadata', requiresRunning: true }],
    ['trino', { label: 'Trino UI', requiresRunning: true }],
  ])

  return services
    .flatMap((service) => {
      const workbench = browserWorkbenches.get(service.id)
      if (!workbench) return []
      if (workbench.requiresRunning && service.status !== 'running') return []
      const firstLink = chooseWorkbenchLink(
        service.links,
        workbench.preferredPortLabel,
      )
      if (!firstLink?.url) return []
      return [
        {
          service: service.name,
          label: workbench.label,
          status: service.status,
          url: withPath(firstLink.url, workbench.path),
          host: readableHost(firstLink.url),
          description: describeWorkbench(service.id),
          initials: serviceInitials(service.name),
        },
      ]
    })
    .slice(0, 6)
}

function chooseWorkbenchLink(
  links: Array<V2Service['links'][number]>,
  preferredPortLabel?: string,
) {
  if (!links.length) return null

  const preferred = preferredPortLabel
    ? links.find((link) => link.label === preferredPortLabel)
    : null
  const projectLink = links.at(-1)

  return projectLink ?? preferred ?? links[0]
}

function describeWorkbench(serviceId: string): string {
  const descriptions: Record<string, string> = {
    dagster: 'Pipeline runs and schedules',
    grafana: 'Metrics and service dashboards',
    hasura: 'Metadata graph and API console',
    minio: 'Lakehouse object storage',
    observatory: 'Current Phlo control plane',
    openmetadata: 'Catalog and ownership',
    'phlo-api': 'Phlo API contract and probes',
    pgweb: 'Postgres metadata browser',
    superset: 'Analytics workspace',
    trino: 'Distributed SQL console',
  }
  return descriptions[serviceId] ?? 'Native service workbench'
}

function readableHost(url: string): string {
  try {
    return new URL(url).host
  } catch {
    return url.replace(/^https?:\/\//, '')
  }
}

function serviceInitials(name: string): string {
  const words = name.replace(/[-_]/g, ' ').trim().split(/\s+/)
  if (words.length === 0 || !words[0]) return 'PH'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return words
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
}

function withPath(url: string, path?: string): string {
  if (!path) return url
  try {
    const parsed = new URL(url)
    parsed.pathname = path
    return parsed.toString()
  } catch {
    return url
  }
}

function failureReason(operation: V2Operation): string | undefined {
  return (
    firstTextMetric(operation.metadata, [
      'exception_message',
      'failure_reason',
      'error',
      'reason',
      'message',
    ]) ??
    operation.health.message ??
    undefined
  )
}

function firstTextMetric(
  metadata: Record<string, NonNullable<unknown>>,
  keys: Array<string>,
): string | undefined {
  for (const key of keys) {
    const value = metadata[key]
    if (typeof value === 'string' && value.trim()) return value
  }
  return undefined
}

function inferStage(asset: V2Asset): string {
  const raw = [
    asset.group,
    asset.id,
    asset.name,
    asset.metadata.stage,
    asset.metadata.namespace,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
  if (raw.includes('bronze') || raw.includes('raw')) return 'bronze'
  if (raw.includes('silver') || raw.includes('clean')) return 'silver'
  if (
    raw.includes('gold') ||
    raw.includes('analytics') ||
    raw.includes('mart')
  ) {
    return 'gold'
  }
  if (
    raw.includes('serving') ||
    raw.includes('api') ||
    raw.includes('publish')
  ) {
    return 'serving'
  }
  return raw.includes('source') || raw.includes('input') ? 'source' : 'gold'
}

function readNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function stageLabel(stage: string): string {
  return stage.charAt(0).toUpperCase() + stage.slice(1)
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
        href: '/services',
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
            href: '/quality',
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
            href: `/operations?operationId=${encodeURIComponent(operation.id)}`,
            kind: 'operation',
            label: operation.name,
            meta:
              failureReason(operation) ??
              operation.target?.label ??
              operation.kind,
            state: 'error',
          }))),
    ...(enabled?.logs === false
      ? []
      : logs
          .filter((log) => log.level === 'error')
          .slice(0, 2)
          .map((log) => ({
            id: `log:${log.id}`,
            href: '/logs',
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

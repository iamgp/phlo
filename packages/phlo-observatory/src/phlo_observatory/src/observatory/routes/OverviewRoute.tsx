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
  ObservatoryAsset,
  ObservatoryBranch,
  ObservatoryCapabilities,
  ObservatoryLogEvent,
  ObservatoryOperation,
  ObservatoryOverview,
  ObservatoryQualityCheck,
  ObservatoryResourceResult,
  ObservatoryService,
} from '@/observatory/api/types'
import {
  getObservatoryAssetRecords,
  getObservatoryLogRecords,
  getObservatoryOperationRecords,
  getObservatoryOverview,
  getObservatoryQualityRecords,
  getObservatoryServices,
} from '@/observatory/api/resources'
import { StatusBadge } from '@/observatory/components/StatusBadge'
import { loadCachedResource } from '@/observatory/routes/liveResource'

const formatter = new Intl.NumberFormat('en')
const refreshTimeFormatter = new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit',
  hour12: false,
  minute: '2-digit',
  second: '2-digit',
  timeZone: 'UTC',
})
const emptyResult = { data: null, error: null }
const stageTransitions = ['ingest', 'normalize', 'model', 'publish']

type OverviewState = {
  assets: ObservatoryResourceResult<Array<ObservatoryAsset>>
  branches: ObservatoryResourceResult<Array<ObservatoryBranch>>
  capabilities: ObservatoryResourceResult<ObservatoryCapabilities> | null
  logs: ObservatoryResourceResult<Array<ObservatoryLogEvent>>
  operations: ObservatoryResourceResult<Array<ObservatoryOperation>>
  overview: ObservatoryResourceResult<ObservatoryOverview>
  quality: ObservatoryResourceResult<Array<ObservatoryQualityCheck>>
  services: ObservatoryResourceResult<Array<ObservatoryService>>
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
      getObservatoryOverview(),
      getObservatoryServices(),
      getObservatoryOperationRecords(),
      getObservatoryAssetRecords(),
      getObservatoryQualityRecords(),
      getObservatoryLogRecords(),
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

    function load(force = false) {
      const empty = { data: [], error: null }

      loadCachedResource('v2:services', getObservatoryServices, {
        force,
        staleMs: 60_000,
      }).then((nextServices) => {
        if (!cancelled) {
          setOverviewState({ services: nextServices, updatedAt: new Date() })
        }
      })

      loadCachedResource('v2:operations', getObservatoryOperationRecords, {
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

      loadCachedResource('v2:assets', getObservatoryAssetRecords, {
        force,
        staleMs: 60_000,
      }).then((nextAssets) => {
        if (!cancelled) {
          setOverviewState({ assets: nextAssets, updatedAt: new Date() })
        }
      })

      loadCachedResource('v2:quality', getObservatoryQualityRecords, {
        force,
        staleMs: 60_000,
      }).then((nextQuality) => {
        if (!cancelled) {
          setOverviewState({ quality: nextQuality, updatedAt: new Date() })
        }
      })

      loadCachedResource('v2:logs', getObservatoryLogRecords, {
        force,
        staleMs: 30_000,
      }).then((nextLogs) => {
        if (!cancelled) {
          setOverviewState({ logs: nextLogs, updatedAt: new Date() })
        }
      })

      setOverviewState({ branches: empty, capabilities: null })
      loadCachedResource('v2:overview', getObservatoryOverview, {
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
    <div className="phlo-observatory-content">
      <header className="phlo-observatory-section-header">
        <div>
          <div className="phlo-observatory-kicker">Overview</div>
          <h1 className="phlo-observatory-title">Lakehouse control</h1>
          <p className="phlo-observatory-subtitle">
            The cross-domain queue: what needs attention, why it matters, and
            where to move next.
          </p>
        </div>
        <StatusBadge
          label={derivedHealth?.message ?? 'API pending'}
          state={derivedHealth?.state ?? (apiError ? 'warning' : 'unknown')}
        />
      </header>

      <section className="phlo-observatory-grid" aria-label="Platform counters">
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

      <section
        className="phlo-observatory-lakehouse-map"
        aria-label="Lakehouse map"
      >
        <div className="phlo-observatory-map-header">
          <h2>Lakehouse map</h2>
          <Link className="phlo-observatory-map-action" to="/workflows/new">
            <Workflow className="size-4" />
            Build workflow
          </Link>
        </div>
        <div className="phlo-observatory-flow-stage-map">
          {lakehouseStages.map((stage, index) => (
            <Link
              className="phlo-observatory-stage-card"
              data-state={stage.state}
              data-transition={stageTransitions[index] ?? ''}
              key={stage.id}
              to={stage.href}
            >
              <div className="phlo-observatory-stage-card-top">
                <span>{stage.label}</span>
                <StatusBadge label={stage.state} state={stage.state} />
              </div>
              <div className="phlo-observatory-stage-body">
                <div className="phlo-observatory-stage-primary">
                  <strong>{formatter.format(stage.records)}</strong>
                  <span>records</span>
                </div>
                <small>
                  {stage.assets} assets · {stage.datasets} datasets ·{' '}
                  {stage.blocking} checks
                </small>
              </div>
              <div className="phlo-observatory-stage-samples">
                {stage.samples.length > 0 ? (
                  stage.samples.map((sample) => (
                    <span key={`${stage.id}:${sample}`}>{sample}</span>
                  ))
                ) : (
                  <span>No assets mapped yet</span>
                )}
              </div>
              <div className="phlo-observatory-stage-meter">
                <span style={{ width: `${stage.weight}%` }} />
              </div>
            </Link>
          ))}
        </div>
        <div className="phlo-observatory-evidence-grid">
          <div className="phlo-observatory-evidence-panel">
            <div className="phlo-observatory-panel-header">
              <h2 className="phlo-observatory-panel-title">Event story</h2>
              <span className="phlo-observatory-pill">
                <GitCommitHorizontal className="size-3.5" />
                {eventStory.events.length || 'Empty'}
              </span>
            </div>
            <div className="phlo-observatory-list">
              {eventStory.events.length > 0 ? (
                eventStory.events.map((event) => (
                  <Link
                    className="phlo-observatory-row"
                    data-state={event.state}
                    key={event.id}
                    to={event.href}
                  >
                    <div className="phlo-observatory-row-main">
                      <div className="phlo-observatory-row-title">
                        <span
                          className="phlo-observatory-dot"
                          data-state={event.state}
                        />
                        <span>{event.label}</span>
                      </div>
                      <div className="phlo-observatory-row-meta">
                        {event.meta}
                      </div>
                      {event.reason && (
                        <div className="phlo-observatory-row-evidence">
                          {event.reason}
                        </div>
                      )}
                    </div>
                    <span className="phlo-observatory-pill">{event.kind}</span>
                  </Link>
                ))
              ) : (
                <EmptyRow label="No events yet" />
              )}
              {eventStory.suppressed > 0 && (
                <div className="phlo-observatory-noise-row">
                  {eventStory.suppressed} platform-noise events suppressed
                </div>
              )}
            </div>
          </div>
          <div className="phlo-observatory-evidence-panel">
            <div className="phlo-observatory-panel-header">
              <h2 className="phlo-observatory-panel-title">
                Native workbenches
              </h2>
              <span className="phlo-observatory-pill">
                <Database className="size-3.5" />
                {integrationLinks.length || 'None'}
              </span>
            </div>
            <div className="phlo-observatory-integration-grid">
              {integrationLinks.length > 0 ? (
                integrationLinks.map((link) => (
                  <a
                    className="phlo-observatory-integration-link"
                    data-state={link.status}
                    href={link.url}
                    key={`${link.service}:${link.label}:${link.url}`}
                    rel="noreferrer"
                    target="_blank"
                  >
                    <span className="phlo-observatory-integration-mark">
                      {link.initials}
                    </span>
                    <span className="phlo-observatory-integration-copy">
                      <strong>{link.label}</strong>
                      <span className="phlo-observatory-integration-meta">
                        <span>{link.service}</span>
                        <span>{link.description}</span>
                      </span>
                      <code>{link.host}</code>
                    </span>
                    <span className="phlo-observatory-integration-status">
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

      <section className="phlo-observatory-command">
        <div className="phlo-observatory-command-primary">
          <div className="phlo-observatory-panel">
            <div className="phlo-observatory-panel-header">
              <h2 className="phlo-observatory-panel-title">Attention queue</h2>
              <span className="phlo-observatory-pill">
                <Activity className="size-3.5" />
                {attentionItems.length || 'Clear'}
              </span>
            </div>
            <div className="phlo-observatory-list">
              {attentionItems.length > 0 ? (
                attentionItems.map((item) => (
                  <a
                    className="phlo-observatory-row"
                    href={item.href}
                    key={item.id}
                  >
                    <div className="phlo-observatory-row-main">
                      <div className="phlo-observatory-row-title">
                        <span
                          className="phlo-observatory-dot"
                          data-state={item.state}
                        />
                        <span>{item.label}</span>
                      </div>
                      <div className="phlo-observatory-row-meta">
                        {item.meta}
                      </div>
                    </div>
                    <span className="phlo-observatory-pill">{item.kind}</span>
                  </a>
                ))
              ) : (
                <EmptyRow label="No active attention items" />
              )}
            </div>
          </div>

          <section className="phlo-observatory-diff-metrics">
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

        <aside className="phlo-observatory-inspector">
          <div className="phlo-observatory-inspector-label">
            Control context
          </div>
          <h2>{derivedHealth?.message ?? 'Waiting for API snapshot'}</h2>
          <p>
            Last refreshed{' '}
            {updatedAt
              ? refreshTimeFormatter.format(updatedAt)
              : 'after first load'}
            .
          </p>
          <dl className="phlo-observatory-facts">
            <Fact
              label="Services needing attention"
              value={attentionServices}
            />
            <Fact label="Blocking checks" value={blockingChecks} />
            <Fact label="Failed operations" value={failedOperations} />
            <Fact label="Error logs" value={errorLogs} />
          </dl>
          <div className="phlo-observatory-detail-list">
            {recentEvidence.length > 0 ? (
              recentEvidence.map((log) => (
                <div className="phlo-observatory-mini-row" key={log.id}>
                  <span>{log.message}</span>
                  <small>
                    {[log.level, log.source, log.timestamp]
                      .filter(Boolean)
                      .join(' · ')}
                  </small>
                </div>
              ))
            ) : (
              <div className="phlo-observatory-mini-row">
                <span>No recent evidence</span>
                <small>
                  Logs will appear as Phlo and stack services emit events.
                </small>
              </div>
            )}
          </div>
          {apiError && (
            <div className="phlo-observatory-panel-footer">{apiError}</div>
          )}
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
    <div className="phlo-observatory-tile">
      <div className="phlo-observatory-tile-label">
        <span>{label}</span>
        {icon}
      </div>
      <div className="phlo-observatory-tile-value">{value}</div>
      <div className="phlo-observatory-tile-note">{note}</div>
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
    <Link className="phlo-observatory-diff-metric" to={href}>
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
    <div className="phlo-observatory-row">
      <div className="phlo-observatory-row-main">
        <div className="phlo-observatory-row-title">{label}</div>
        <div className="phlo-observatory-row-meta">
          Connect a running lakehouse or add resources to populate this surface.
        </div>
      </div>
    </div>
  )
}

function buildLakehouseStages(
  assets: Array<ObservatoryAsset>,
  quality: Array<ObservatoryQualityCheck>,
) {
  const stageOrder = ['source', 'bronze', 'silver', 'gold', 'serving']
  const stages = new Map(
    stageOrder.map((stage) => [
      stage,
      {
        id: stage,
        label: stageLabel(stage),
        assets: 0,
        datasets: 0,
        records: 0,
        blocking: 0,
        state: 'unknown' as 'ok' | 'warning' | 'error' | 'unknown',
        href: stage === 'serving' ? '/apis' : '/data',
        weight: 8,
        samples: [] as Array<string>,
      },
    ]),
  )
  const qualityByAsset = new Map<string, Array<ObservatoryQualityCheck>>()
  for (const check of quality) {
    const checks = qualityByAsset.get(check.asset_id)
    if (checks) {
      checks.push(check)
    } else {
      qualityByAsset.set(check.asset_id, [check])
    }
  }

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
    const checks = qualityByAsset.get(asset.id) ?? []
    const hasFailingCheck = checks.some((check) => check.status === 'failing')
    const hasWarningCheck = checks.some((check) => check.status === 'warning')
    const blockingChecks = checks.filter((check) => check.blocking).length
    stage.assets += 1
    stage.datasets += tables
    stage.records += records
    stage.blocking += blockingChecks
    if (stage.samples.length < 3) stage.samples.push(asset.name)
    if (hasFailingCheck) stage.state = 'error'
    else if (hasWarningCheck && stage.state !== 'error') {
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
  operations: Array<ObservatoryOperation>,
  logs: Array<ObservatoryLogEvent>,
) {
  const operationEvents = operations.map((operation) => ({
    id: `operation:${operation.id}`,
    href: `/operations?operationId=${encodeURIComponent(operation.id)}`,
    label: operation.name,
    kind: 'operation',
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
  const visibleLogs = logs.filter(isFrontPageLog)
  const suppressedLogs = logs.filter((log) => !isFrontPageLog(log))
  const logEvents = logs.filter(isFrontPageLog).map((log) => ({
    id: `log:${log.id}`,
    href: '/logs',
    label: log.message,
    kind: 'log',
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
    suppressed: suppressedLogs.length,
  }
}

function scoreOperation(operation: ObservatoryOperation): number {
  let score = 20
  if (operation.kind.startsWith('pipeline')) score += 50
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

function scoreLog(log: ObservatoryLogEvent): number {
  let score = 5
  if (log.level === 'error') score += 40
  if (log.level === 'warning') score += 20
  if (
    log.resource?.kind === 'asset' ||
    log.resource?.kind === 'data_product' ||
    log.resource?.kind === 'table'
  ) {
    score += 20
  }
  if (log.source?.toLowerCase().includes('keystone')) score += 20
  return score
}

function isFrontPageLog(log: ObservatoryLogEvent): boolean {
  return !isNoisyLog(log) && Boolean(log.resource)
}

function isNoisyLog(log: ObservatoryLogEvent): boolean {
  const message = log.message.toLowerCase()
  const source = log.source?.toLowerCase() ?? ''
  const event = String(log.metadata?.event ?? '').toLowerCase()
  return [
    'failed_to_discover_user_workflows',
    'hasura_using_generated_default_admin_secret',
    'no heartbeat received',
    'optional_capability_degraded',
    'unknown_plugin_type',
    'plugin_load_failed',
    'plugin_registry_fetch_fallback',
    'observatory_settings_falling_back_to_memory',
    'using the generated default hasura admin secret',
    'workflows directory not found',
  ].some(
    (needle) =>
      message.includes(needle) ||
      source.includes(needle) ||
      event.includes(needle),
  )
}

function buildIntegrationLinks(services: Array<ObservatoryService>) {
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
  links: Array<ObservatoryService['links'][number]>,
  preferredPortLabel?: string,
) {
  if (!links.length) return null

  const preferred = preferredPortLabel
    ? links.find((link) => link.label === preferredPortLabel)
    : null
  const projectLink = links.at(-1)

  return preferred ?? projectLink ?? links[0]
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

function failureReason(operation: ObservatoryOperation): string | undefined {
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

function inferStage(asset: ObservatoryAsset): string {
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
  services: Array<ObservatoryService>
  operations: Array<ObservatoryOperation>
  quality: Array<ObservatoryQualityCheck>
  logs: Array<ObservatoryLogEvent>
  enabled?: Record<string, boolean>
}) {
  const qualityResourceIds = new Set(
    quality
      .filter((check) => check.status !== 'passing')
      .map((check) => check.asset_id),
  )
  const failedOperationResourceIds = new Set(
    operations
      .filter((operation) => operation.status === 'failed')
      .map((operation) => operation.target?.id)
      .filter(Boolean),
  )

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
          .filter((check) => check.status !== 'passing')
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
          .filter(
            (log) =>
              log.level === 'error' &&
              isFrontPageLog(log) &&
              !qualityResourceIds.has(log.resource?.id ?? '') &&
              !failedOperationResourceIds.has(log.resource?.id ?? ''),
          )
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
  capabilities: ObservatoryCapabilities | null | undefined,
  key: string,
): boolean {
  if (!capabilities) return true
  return capabilities.features[key] !== false
}

function serviceNeedsAttention(service: ObservatoryService): boolean {
  if (service.health.state === 'error' || service.health.state === 'warning') {
    return true
  }
  if (service.status === 'unhealthy') return true
  return service.status === 'stopped' && service.health.state !== 'ok'
}

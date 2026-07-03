import { createFileRoute } from '@tanstack/react-router'
import { AlertTriangle, CircleHelp, Shield, ShieldCheck } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryQualityCheck,
  ObservatoryQualityDetail,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import type {
  ObservatoryFlowEdge,
  ObservatoryFlowNode,
} from '@/observatory/components/ObservatoryFlowCanvas'
import {
  getObservatoryQualityDetail,
  getObservatoryQualityDetailDirect,
  getObservatoryQualityRecords,
  runObservatoryAction,
} from '@/observatory/api/resources'
import { ActionButton } from '@/observatory/components/ActionButton'
import { ObservatoryFlowCanvas } from '@/observatory/components/ObservatoryFlowCanvas'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import {
  invalidateCachedResources,
  loadCachedResource,
  useLiveResource,
} from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/quality')({
  component: Quality,
})

export function Quality() {
  const result = useLiveResource(
    getObservatoryQualityRecords,
    120_000,
    'v2:quality',
  )
  const checks = result.data ?? []
  const sortedChecks = useMemo(() => [...checks].sort(compareQuality), [checks])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<QualityView>('queue')
  const blocking = checks.filter((check) => check.blocking).length
  const warnings = checks.filter((check) => check.status === 'warning').length
  const unknown = checks.filter((check) => check.status === 'unknown').length
  const failing = checks.filter((check) => check.status === 'failing').length
  const observed = checks.length - unknown
  const score = observed
    ? Math.round(((observed - failing) / observed) * 100)
    : null
  const selected =
    sortedChecks.find((check) => check.id === selectedId) ??
    sortedChecks[0] ??
    null
  const [detail, setDetail] = useState<
    ObservatoryResourceResult<ObservatoryQualityDetail>
  >({
    data: null,
    error: null,
  })
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const graph = useMemo(() => buildQualityGraph(sortedChecks), [sortedChecks])

  useEffect(() => {
    if (selectedId !== null || sortedChecks.length === 0) return
    setSelectedId(sortedChecks[0].id)
  }, [selectedId, sortedChecks])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    const loadDetail =
      typeof window === 'undefined'
        ? () => getObservatoryQualityDetail({ data: { checkId: selected.id } })
        : () => getObservatoryQualityDetailDirect({ checkId: selected.id })

    void loadCachedResource(`v2:quality-detail:${selected.id}`, loadDetail, {
      staleMs: 120_000,
    }).then((next) => {
      if (!cancelled) setDetail(next)
    })
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <ObservatoryPage
      kicker="Quality"
      title="Quality issues"
      description="Review failing, warning, and not-yet-observed checks as one operational queue."
      action={
        <span className="phlo-observatory-pill">{checks.length} checks</span>
      }
    >
      <section className="phlo-observatory-quality-shell">
        <div className="phlo-observatory-quality-board">
          <div className="phlo-observatory-quality-score">
            <strong>{score === null ? '—' : score}</strong>
            <span>Observed health</span>
            <small>
              {observed} observed · {failing} failing · {unknown} pending
            </small>
          </div>
          <div className="phlo-observatory-command-strip">
            <Metric
              icon={<Shield className="size-4" />}
              label="Blocking"
              value={blocking}
            />
            <Metric
              icon={<AlertTriangle className="size-4" />}
              label="Warnings"
              value={warnings}
            />
            <Metric
              icon={<CircleHelp className="size-4" />}
              label="Not observed"
              value={unknown}
            />
          </div>
          <div className="phlo-observatory-data-main-tabs" role="tablist">
            {qualityViews.map((view) => (
              <button
                aria-selected={activeView === view.id}
                data-active={activeView === view.id}
                key={view.id}
                onClick={() => setActiveView(view.id)}
                role="tab"
                type="button"
              >
                {view.icon}
                {view.label}
              </button>
            ))}
          </div>
          {activeView === 'graph' ? (
            <div className="phlo-observatory-flow-band">
              <div className="phlo-observatory-workspace-toolbar">
                <span>Issue graph</span>
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
            <div className="phlo-observatory-check-list">
              {sortedChecks.map((check) => (
                <CheckRow
                  key={check.id}
                  check={check}
                  onSelect={setSelectedId}
                  selected={check.id === selected?.id}
                />
              ))}
              {checks.length === 0 && (
                <div className="phlo-observatory-empty-state">
                  No quality checks registered yet.
                </div>
              )}
            </div>
          )}
        </div>

        <aside className="phlo-observatory-inspector">
          <div className="phlo-observatory-inspector-label">Triage context</div>
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p>{selected.description ?? selected.asset_id}</p>
              <dl className="phlo-observatory-facts">
                <Fact label="Asset" value={selected.asset_id} />
                <Fact
                  label="Severity"
                  value={selected.severity ?? 'unspecified'}
                />
                <Fact
                  label="Blocking"
                  value={selected.blocking ? 'yes' : 'no'}
                />
                <Fact label="Status" value={qualityStatusLabel(selected)} />
                <Fact label="Owner" value={readMetadata(selected, 'owner')} />
              </dl>
              <div className="phlo-observatory-detail-list">
                {urgentReason(selected) && (
                  <div className="phlo-observatory-mini-row">
                    <span>Why it matters</span>
                    <small>{urgentReason(selected)}</small>
                  </div>
                )}
                <div className="phlo-observatory-mini-row">
                  <span>Latest result</span>
                  <small>{qualityResultSummary(selected)}</small>
                </div>
                <div className="phlo-observatory-mini-row">
                  <span>Asset detail</span>
                  <small>
                    {detail.data?.asset?.description ??
                      detail.data?.asset?.group ??
                      'No linked asset detail returned'}
                  </small>
                </div>
                <div className="phlo-observatory-mini-row">
                  <span>History</span>
                  <small>{detail.data?.history.length ?? 0} executions</small>
                </div>
                <div className="phlo-observatory-mini-row">
                  <span>Logs</span>
                  <small>{detail.data?.logs.length ?? 0} linked events</small>
                </div>
                <div className="phlo-observatory-mini-row">
                  <span>Actions</span>
                  <small>{qualityActionsSummary(detail.data)}</small>
                </div>
              </div>
              {(detail.data?.actions ?? []).length > 0 && (
                <div className="phlo-observatory-action-row">
                  {(detail.data?.actions ?? []).map((action) => (
                    <ActionButton
                      action={action}
                      key={action.id}
                      onRun={(actionId) => {
                        void runObservatoryAction({ data: { actionId } }).then(
                          (next) => {
                            invalidateCachedResources([
                              'v2:operations',
                              'v2:quality',
                            ])
                            setActionMessage(
                              next.data?.message ??
                                next.error ??
                                'Action requested',
                            )
                          },
                        )
                      }}
                    />
                  ))}
                </div>
              )}
              {actionMessage && (
                <div className="phlo-observatory-panel-footer">
                  {actionMessage}
                </div>
              )}
            </>
          ) : (
            <p>No quality check selected.</p>
          )}
          {detail.error && (
            <div className="phlo-observatory-panel-footer">{detail.error}</div>
          )}
          {result.error && (
            <div className="phlo-observatory-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </ObservatoryPage>
  )
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: string | number
}) {
  return (
    <div className="phlo-observatory-command-metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

type QualityView = 'queue' | 'graph'

const qualityViews: Array<{
  id: QualityView
  label: string
  icon: ReactNode
}> = [
  { id: 'queue', label: 'Queue', icon: <ShieldCheck className="size-3.5" /> },
  { id: 'graph', label: 'Graph', icon: <AlertTriangle className="size-3.5" /> },
]

function CheckRow({
  check,
  onSelect,
  selected,
}: {
  check: ObservatoryQualityCheck
  onSelect: (id: string) => void
  selected: boolean
}) {
  return (
    <button
      className="phlo-observatory-check-row"
      data-active={selected}
      onClick={() => onSelect(check.id)}
      type="button"
    >
      <span
        className="phlo-observatory-dot"
        data-state={
          check.status === 'failing'
            ? 'error'
            : check.status === 'unknown'
              ? 'warning'
              : check.status
        }
      />
      <div>
        <div className="phlo-observatory-row-title">
          <ShieldCheck className="size-4" />
          {check.name}
        </div>
        <div className="phlo-observatory-row-meta">{check.asset_id}</div>
      </div>
      <span className="phlo-observatory-pill">{qualityStatusLabel(check)}</span>
      <span className="phlo-observatory-pill">
        {check.severity ?? qualityStatusLabel(check)}
      </span>
      <span className="phlo-observatory-pill">
        {check.blocking ? 'blocking' : 'advisory'}
      </span>
    </button>
  )
}

function buildQualityGraph(checks: Array<ObservatoryQualityCheck>): {
  nodes: Array<ObservatoryFlowNode>
  edges: Array<ObservatoryFlowEdge>
} {
  const assetNodes = Array.from(
    new Set(checks.map((check) => check.asset_id)),
  ).map((asset): ObservatoryFlowNode => ({
    id: `asset:${asset}`,
    label: asset,
    kind: 'asset',
    lane: 'table',
    selectId: checks.find((check) => check.asset_id === asset)?.id,
    subtitle: 'protected asset',
  }))

  const checkNodes = checks.map((check): ObservatoryFlowNode => ({
    id: check.id,
    label: check.name,
    kind: 'quality',
    lane: 'quality',
    subtitle: check.asset_id,
    metric: `${check.severity ?? qualityStatusLabel(check)} · ${check.blocking ? 'blocking' : 'advisory'}`,
  }))

  const edges = checks.map((check): ObservatoryFlowEdge => ({
    id: `${check.asset_id}->${check.id}`,
    source: `asset:${check.asset_id}`,
    target: check.id,
  }))

  return { nodes: [...assetNodes, ...checkNodes], edges }
}

function compareQuality(
  left: ObservatoryQualityCheck,
  right: ObservatoryQualityCheck,
): number {
  return qualityUrgency(right) - qualityUrgency(left)
}

function qualityUrgency(check: ObservatoryQualityCheck): number {
  let score = 0
  if (check.status === 'failing') score += 100
  if (check.blocking) score += 30
  if (check.status === 'warning') score += 20
  if (check.status === 'unknown') score += 10
  if (check.severity === 'critical') score += 25
  if (check.severity === 'high') score += 15
  if (check.severity === 'medium') score += 5
  return score
}

function qualityStatusLabel(check: ObservatoryQualityCheck): string {
  if (check.status === 'unknown') return 'not observed'
  return check.status
}

function qualityResultSummary(check: ObservatoryQualityCheck): string {
  if (check.status === 'unknown') {
    return 'No quality result has been recorded for this check yet.'
  }
  if (check.status === 'passing') return 'Latest observed run passed.'
  if (check.status === 'warning') return 'Latest observed run raised a warning.'
  return 'Latest observed run failed.'
}

function qualityActionsSummary(
  detail: ObservatoryQualityDetail | null,
): string {
  const actions = detail?.actions ?? []
  const enabled = actions.filter((action) => action.enabled)
  if (enabled.length === 0) return 'No guarded quality mutation exposed.'
  return enabled.map((action) => action.label).join(', ')
}

function urgentReason(check: ObservatoryQualityCheck): string | null {
  const explicit =
    readMetadata(check, 'last_failure') ??
    readMetadata(check, 'failure_reason') ??
    readMetadata(check, 'message')
  if (explicit !== 'n/a') return explicit
  if (check.status === 'failing' && check.blocking) {
    return 'This blocking check is failing and should stop promotion.'
  }
  if (check.status === 'warning')
    return 'This check is warning and needs review.'
  if (check.status === 'unknown') return 'No recent evidence has been reported.'
  return null
}

function readMetadata(check: ObservatoryQualityCheck, key: string): string {
  const value = check.metadata[key]
  if (value === null || value === undefined || value === '') return 'n/a'
  return String(value)
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

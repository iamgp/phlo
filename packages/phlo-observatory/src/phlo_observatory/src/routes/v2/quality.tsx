import { createFileRoute } from '@tanstack/react-router'
import { AlertTriangle, CircleHelp, Shield, ShieldCheck } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2QualityCheck,
  V2QualityDetail,
  V2ResourceResult,
} from '@/v2/api/types'
import type { V2FlowEdge, V2FlowNode } from '@/v2/components/V2FlowCanvas'
import { getV2QualityDetail, getV2QualityRecords } from '@/v2/api/resources'
import { V2FlowCanvas } from '@/v2/components/V2FlowCanvas'
import { V2Page } from '@/v2/components/V2Page'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/quality')({
  component: Quality,
})

function Quality() {
  const result = useLiveResource(getV2QualityRecords)
  const checks = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const blocking = checks.filter((check) => check.blocking).length
  const warnings = checks.filter((check) => check.severity === 'warning').length
  const unknown = checks.filter((check) => check.status === 'unknown').length
  const failing = checks.filter((check) => check.status === 'failing').length
  const observed = checks.length - unknown
  const score = observed
    ? Math.round(((observed - failing) / observed) * 100)
    : null
  const selected =
    checks.find((check) => check.id === selectedId) ?? checks[0] ?? null
  const [detail, setDetail] = useState<V2ResourceResult<V2QualityDetail>>({
    data: null,
    error: null,
  })
  const graph = useMemo(() => buildQualityGraph(checks), [checks])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getV2QualityDetail({ data: { checkId: selected.id } }).then((next) => {
      if (!cancelled) setDetail(next)
    })
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <V2Page
      kicker="Issues"
      title="Data issues"
      description="Triage quality, freshness, and blocking trust signals by asset."
      action={<span className="phlo-v2-pill">{checks.length} checks</span>}
    >
      <section className="phlo-v2-quality-shell">
        <div className="phlo-v2-quality-board">
          <div className="phlo-v2-quality-score">
            <strong>{score === null ? '—' : score}</strong>
            <span>Observed pass rate</span>
            <small>
              {observed} observed · {failing} failing · {unknown} not observed
            </small>
          </div>
          <div className="phlo-v2-flow-band">
            <div className="phlo-v2-workspace-toolbar">
              <span>Issue graph</span>
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
          <div className="phlo-v2-command-strip">
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
          <div className="phlo-v2-check-list">
            {checks.map((check) => (
              <CheckRow
                key={check.id}
                check={check}
                onSelect={setSelectedId}
                selected={check.id === selected?.id}
              />
            ))}
            {checks.length === 0 && (
              <div className="phlo-v2-empty-state">
                No quality checks registered yet.
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Triage context</div>
          {selected ? (
            <>
              <h2>{selected.name}</h2>
              <p>{selected.description ?? selected.asset_id}</p>
              <dl className="phlo-v2-facts">
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
              </dl>
              <div className="phlo-v2-detail-list">
                <div className="phlo-v2-mini-row">
                  <span>Execution result</span>
                  <small>{qualityResultSummary(selected)}</small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>Asset detail</span>
                  <small>
                    {detail.data?.asset?.description ??
                      detail.data?.asset?.group ??
                      'No linked asset detail returned'}
                  </small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>History</span>
                  <small>{detail.data?.history.length ?? 0} executions</small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>Logs</span>
                  <small>{detail.data?.logs.length ?? 0} linked events</small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>Available actions</span>
                  <small>{qualityActionsSummary(detail.data)}</small>
                </div>
              </div>
            </>
          ) : (
            <p>No quality check selected.</p>
          )}
          {detail.error && (
            <div className="phlo-v2-panel-footer">{detail.error}</div>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
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
    <div className="phlo-v2-command-metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function CheckRow({
  check,
  onSelect,
  selected,
}: {
  check: V2QualityCheck
  onSelect: (id: string) => void
  selected: boolean
}) {
  return (
    <button
      className="phlo-v2-check-row"
      data-active={selected}
      onClick={() => onSelect(check.id)}
      type="button"
    >
      <span
        className="phlo-v2-dot"
        data-state={
          check.status === 'failing'
            ? 'error'
            : check.status === 'unknown'
              ? 'warning'
              : check.status
        }
      />
      <div>
        <div className="phlo-v2-row-title">
          <ShieldCheck className="size-4" />
          {check.name}
        </div>
        <div className="phlo-v2-row-meta">{check.asset_id}</div>
      </div>
      <span className="phlo-v2-pill">
        {check.severity ?? qualityStatusLabel(check)}
      </span>
      <span className="phlo-v2-pill">
        {check.blocking ? 'blocking' : 'advisory'}
      </span>
    </button>
  )
}

function buildQualityGraph(checks: Array<V2QualityCheck>): {
  nodes: Array<V2FlowNode>
  edges: Array<V2FlowEdge>
} {
  const assetNodes = Array.from(
    new Set(checks.map((check) => check.asset_id)),
  ).map(
    (asset): V2FlowNode => ({
      id: `asset:${asset}`,
      label: asset,
      kind: 'asset',
      lane: 'table',
      subtitle: 'protected asset',
    }),
  )

  const checkNodes = checks.map(
    (check): V2FlowNode => ({
      id: check.id,
      label: check.name,
      kind: 'quality',
      lane: 'quality',
      subtitle: check.asset_id,
      metric: `${check.severity ?? qualityStatusLabel(check)} · ${check.blocking ? 'blocking' : 'advisory'}`,
    }),
  )

  const edges = checks.map(
    (check): V2FlowEdge => ({
      id: `${check.asset_id}->${check.id}`,
      source: `asset:${check.asset_id}`,
      target: check.id,
    }),
  )

  return { nodes: [...assetNodes, ...checkNodes], edges }
}

function qualityStatusLabel(check: V2QualityCheck): string {
  if (check.status === 'unknown') return 'not observed'
  return check.status
}

function qualityResultSummary(check: V2QualityCheck): string {
  if (check.status === 'unknown') {
    return 'No result has been returned by the quality read model yet.'
  }
  if (check.status === 'passing') return 'Latest observed run passed.'
  if (check.status === 'warning') return 'Latest observed run raised a warning.'
  return 'Latest observed run failed.'
}

function qualityActionsSummary(detail: V2QualityDetail | null): string {
  const actions = detail?.actions ?? []
  const enabled = actions.filter((action) => action.enabled)
  if (enabled.length === 0) return 'No guarded quality mutation exposed.'
  return enabled.map((action) => action.label).join(', ')
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

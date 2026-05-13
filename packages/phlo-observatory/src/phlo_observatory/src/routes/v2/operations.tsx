import { createFileRoute } from '@tanstack/react-router'
import { CheckCircle2, Clock3, RotateCcw, ShieldAlert } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2Operation,
  V2OperationDetail,
  V2ResourceResult,
} from '@/v2/api/types'
import type { V2FlowEdge, V2FlowNode } from '@/v2/components/V2FlowCanvas'
import {
  getV2OperationDetail,
  getV2OperationRecords,
  runV2Action,
} from '@/v2/api/resources'
import { ActionButton } from '@/v2/components/ActionButton'
import { V2FlowCanvas } from '@/v2/components/V2FlowCanvas'
import { V2Page } from '@/v2/components/V2Page'
import { readMetric, useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/operations')({
  component: Operations,
})

export function Operations() {
  const result = useLiveResource(
    getV2OperationRecords,
    120_000,
    'v2:operations',
  )
  const operations = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const latest =
    operations.find((operation) => operation.id === selectedId) ??
    operations[0] ??
    null
  const [detail, setDetail] = useState<V2ResourceResult<V2OperationDetail>>({
    data: null,
    error: null,
  })
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const failed = operations.filter(
    (operation) => operation.status === 'failed',
  ).length
  const recovered = operations.filter(
    (operation) => operation.status === 'succeeded',
  ).length
  const graph = useMemo(() => buildOperationGraph(operations), [operations])

  useEffect(() => {
    if (!latest) {
      setDetail({ data: null, error: null })
      return
    }
    let cancelled = false
    void getV2OperationDetail({ data: { operationId: latest.id } }).then(
      (next) => {
        if (!cancelled) setDetail(next)
      },
    )
    return () => {
      cancelled = true
    }
  }, [latest])

  return (
    <V2Page
      kicker="Actions"
      title="Recovery activity"
      description="Phlo-owned actions, maintenance status, and service-impacting work."
      action={<span className="phlo-v2-pill">{operations.length} actions</span>}
    >
      <section className="phlo-v2-command">
        <div className="phlo-v2-command-primary">
          {operations.length > 0 ? (
            <>
              <div className="phlo-v2-flow-band">
                <div className="phlo-v2-workspace-toolbar">
                  <span>Action graph</span>
                  <span className="phlo-v2-pill">
                    {graph.edges.length} links
                  </span>
                </div>
                <V2FlowCanvas
                  edges={graph.edges}
                  nodes={graph.nodes}
                  onSelect={setSelectedId}
                  selectedId={latest?.id}
                />
              </div>
              <div className="phlo-v2-command-strip">
                <Metric
                  icon={<CheckCircle2 className="size-4" />}
                  label="Recovered"
                  value={recovered}
                />
                <Metric
                  icon={<ShieldAlert className="size-4" />}
                  label="Failed"
                  value={failed}
                />
                <Metric
                  icon={<Clock3 className="size-4" />}
                  label="Last duration"
                  value={
                    latest?.duration_seconds
                      ? `${latest.duration_seconds}s`
                      : 'n/a'
                  }
                />
              </div>
              <div className="phlo-v2-timeline">
                {operations.map((operation) => (
                  <OperationLine
                    key={operation.id}
                    onSelect={setSelectedId}
                    operation={operation}
                    selected={operation.id === latest?.id}
                  />
                ))}
              </div>
            </>
          ) : (
            <div className="phlo-v2-operation-empty">
              <div>
                <span className="phlo-v2-inspector-label">
                  No Phlo operations recorded
                </span>
                <h2>Operational history is quiet.</h2>
                <p>
                  Dagster owns asset materialization runs. Observatory will show
                  Phlo recovery, branch, service, and maintenance operations
                  here once phlo-api records them.
                </p>
              </div>
              <div className="phlo-v2-detail-list">
                <div className="phlo-v2-mini-row">
                  <span>Dagster runs</span>
                  <small>Managed in Dagster</small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>Phlo operations</span>
                  <small>0 recorded</small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>Recovery actions</span>
                  <small>No guarded action history yet</small>
                </div>
              </div>
            </div>
          )}
        </div>

        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Selected operation</div>
          {latest ? (
            <>
              <h2>{latest.name}</h2>
              <p>{latest.target?.label ?? latest.kind}</p>
              <dl className="phlo-v2-facts">
                <Fact label="Status" value={latest.status} />
                <Fact
                  label="Namespace"
                  value={readMetric(latest.metadata, 'namespace')}
                />
                <Fact
                  label="Tables"
                  value={readMetric(latest.metadata, 'tables_processed')}
                />
                <Fact
                  label="Records"
                  value={readMetric(latest.metadata, 'total_records')}
                />
                <Fact
                  label="Size"
                  value={`${readMetric(latest.metadata, 'total_size_mb') ?? 0} MB`}
                />
                <Fact
                  label="Completed"
                  value={latest.completed_at ?? 'not completed'}
                />
              </dl>
              <div className="phlo-v2-action-row">
                {(detail.data?.actions ?? []).map((action) => (
                  <ActionButton
                    action={action}
                    key={action.id}
                    onRun={(actionId) => {
                      void runV2Action({ data: { actionId } }).then((next) => {
                        setActionMessage(
                          next.data?.message ??
                            next.error ??
                            'Action requested',
                        )
                      })
                    }}
                  />
                ))}
              </div>
              {actionMessage && (
                <div className="phlo-v2-panel-footer">{actionMessage}</div>
              )}
              <div className="phlo-v2-detail-list">
                <div className="phlo-v2-mini-row">
                  <span>Related</span>
                  <small>
                    {detail.data?.related
                      .map((item) => item.label)
                      .join(', ') || 'none'}
                  </small>
                </div>
                <div className="phlo-v2-mini-row">
                  <span>Logs</span>
                  <small>{detail.data?.logs.length ?? 0} linked events</small>
                </div>
              </div>
            </>
          ) : (
            <>
              <h2>No operation selected</h2>
              <p>There are no Phlo operation records for this lakehouse yet.</p>
            </>
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

function OperationLine({
  operation,
  onSelect,
  selected,
}: {
  operation: V2Operation
  onSelect: (id: string) => void
  selected: boolean
}) {
  return (
    <button
      className="phlo-v2-timeline-row"
      data-active={selected}
      onClick={() => onSelect(operation.id)}
      type="button"
    >
      <span className="phlo-v2-dot" data-state={operation.health.state} />
      <div>
        <div className="phlo-v2-row-title">
          <RotateCcw className="size-4" />
          {operation.name}
        </div>
        <div className="phlo-v2-row-meta">
          {operation.kind} · {operation.target?.label ?? 'platform'} ·{' '}
          {operation.completed_at ?? 'in progress'}
        </div>
      </div>
      <span className="phlo-v2-pill">{operation.status}</span>
    </button>
  )
}

function buildOperationGraph(operations: Array<V2Operation>): {
  nodes: Array<V2FlowNode>
  edges: Array<V2FlowEdge>
} {
  const targetById = new Map<string, NonNullable<V2Operation['target']>>()
  const operationIdByTargetId = new Map<string, string>()
  for (const operation of operations) {
    if (operation.target) {
      const targetId = operation.target.id
      if (!targetById.has(targetId)) {
        targetById.set(targetId, operation.target)
        operationIdByTargetId.set(targetId, operation.id)
      }
    }
  }

  const targetNodes = Array.from(targetById.values()).map(
    (target): V2FlowNode => ({
      id: `target:${target.id}`,
      label: target.label,
      kind: target.kind === 'branch' ? 'branch' : 'service',
      lane: 'branch',
      selectId: operationIdByTargetId.get(target.id),
      subtitle: target.kind,
    }),
  )

  const operationNodes = operations.map(
    (operation): V2FlowNode => ({
      id: operation.id,
      label: operation.name,
      kind: 'operation',
      lane: 'operation',
      subtitle: operation.kind,
      metric: `${operation.status} · ${operation.duration_seconds ?? 'n/a'}s`,
    }),
  )

  const edges: Array<V2FlowEdge> = []
  for (const operation of operations) {
    if (operation.target) {
      edges.push({
        id: `${operation.target.id}->${operation.id}`,
        source: `target:${operation.target.id}`,
        target: operation.id,
      })
    }
  }

  return { nodes: [...targetNodes, ...operationNodes], edges }
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

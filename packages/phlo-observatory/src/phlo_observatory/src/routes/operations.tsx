import { createFileRoute } from '@tanstack/react-router'
import {
  CheckCircle2,
  Clock3,
  Database,
  RotateCcw,
  ShieldAlert,
} from 'lucide-react'
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
import {
  invalidateCachedResources,
  readMetric,
  useLiveResource,
} from '@/v2/routes/liveResource'

export const Route = createFileRoute('/operations')({
  component: Operations,
})

export function Operations() {
  const result = useLiveResource(
    getV2OperationRecords,
    120_000,
    'v2:operations',
  )
  const operations = result.data ?? []
  const [localOperations, setLocalOperations] = useState<Array<V2Operation>>([])
  const visibleOperations = mergeOperations(localOperations, operations)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const latest =
    visibleOperations.find((operation) => operation.id === selectedId) ??
    visibleOperations[0] ??
    null
  const displayedOperations = visibleOperations.slice(0, 100)
  const hiddenOperationCount = Math.max(
    0,
    visibleOperations.length - displayedOperations.length,
  )
  const [detail, setDetail] = useState<V2ResourceResult<V2OperationDetail>>({
    data: null,
    error: null,
  })
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const failed = visibleOperations.filter(
    (operation) => operation.status === 'failed',
  ).length
  const recovered = visibleOperations.filter(
    (operation) => operation.status === 'succeeded',
  ).length
  const ledger = useMemo(
    () => buildOperationLedger(visibleOperations),
    [visibleOperations],
  )
  const selectedFailure = latest ? operationFailure(latest) : null
  const selectedMetadata = latest ? operationMetadata(latest) : []
  const selectedIsWap = latest?.kind === 'wap'

  useEffect(() => {
    if (typeof window === 'undefined') return
    const requested = new URLSearchParams(window.location.search).get(
      'operationId',
    )
    if (!requested || requested === selectedId) return
    if (visibleOperations.some((operation) => operation.id === requested)) {
      setSelectedId(requested)
    }
  }, [selectedId, visibleOperations])

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
      kicker="Operations"
      title={selectedIsWap && latest ? latest.name : 'Recovery activity'}
      description={
        selectedIsWap && latest
          ? 'WAP branch publish evidence, affected tables, and target hash movement.'
          : 'Phlo-owned actions, maintenance status, and service-impacting work.'
      }
      action={
        <span className="phlo-v2-pill">{visibleOperations.length} actions</span>
      }
    >
      <section
        className={`phlo-v2-command${
          selectedIsWap ? ' phlo-v2-wap-operation-shell' : ''
        }`}
      >
        <div className="phlo-v2-command-primary">
          {visibleOperations.length > 0 ? (
            <>
              {!selectedIsWap && (
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
              )}
              {latest && selectedIsWap ? (
                <WapOperationFocus operation={latest} />
              ) : latest ? (
                <div
                  className="phlo-v2-operation-focus"
                  data-state={latest.health.state}
                >
                  <div className="phlo-v2-workspace-toolbar">
                    <span>Selected operation evidence</span>
                    <span className="phlo-v2-pill">{latest.status}</span>
                  </div>
                  <div className="phlo-v2-operation-focus-body">
                    <div className="phlo-v2-operation-focus-main">
                      <span className="phlo-v2-inspector-label">
                        {latest.kind}
                      </span>
                      <h2>{latest.name}</h2>
                      <p>{latest.target?.label ?? 'Platform operation'}</p>
                      {selectedFailure && (
                        <div className="phlo-v2-failure-callout">
                          <strong>{selectedFailure.title}</strong>
                          <span>{selectedFailure.message}</span>
                        </div>
                      )}
                    </div>
                    <dl className="phlo-v2-operation-evidence-grid">
                      <Fact label="Operation id" value={latest.id} />
                      <Fact
                        label="Experiment"
                        value={readMetric(latest.metadata, 'experiment_id')}
                      />
                      <Fact
                        label="Plate"
                        value={readMetric(latest.metadata, 'plate_id')}
                      />
                      <Fact
                        label="Completed"
                        value={formatDateTime(latest.completed_at)}
                      />
                    </dl>
                  </div>
                  {selectedMetadata.length > 0 && (
                    <div className="phlo-v2-operation-metadata">
                      {selectedMetadata.map(([key, value]) => (
                        <span key={key}>
                          <strong>{humanizeKey(key)}</strong>
                          {String(value)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
              {!selectedIsWap && (
                <div className="phlo-v2-operation-ledger">
                  <div className="phlo-v2-workspace-toolbar">
                    <span>Target ledger</span>
                    <span className="phlo-v2-pill">
                      {ledger.length} targets
                    </span>
                  </div>
                  <div className="phlo-v2-operation-ledger-grid">
                    {ledger.map((item) => (
                      <button
                        className="phlo-v2-operation-ledger-card"
                        data-state={item.state}
                        key={item.id}
                        onClick={() => setSelectedId(item.latest.id)}
                        type="button"
                      >
                        <span>{item.kind}</span>
                        <strong>{item.label}</strong>
                        <small>
                          {item.succeeded} succeeded · {item.failed} failed ·{' '}
                          {item.lastSeen}
                        </small>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {!selectedIsWap && (
                <>
                  <div className="phlo-v2-workspace-toolbar">
                    <span>Activity stream</span>
                    <span className="phlo-v2-pill">
                      showing {displayedOperations.length}
                      {hiddenOperationCount > 0
                        ? ` of ${visibleOperations.length}`
                        : ''}
                    </span>
                  </div>
                  <div className="phlo-v2-timeline">
                    {displayedOperations.map((operation) => (
                      <OperationLine
                        key={operation.id}
                        onSelect={setSelectedId}
                        operation={operation}
                        selected={operation.id === latest?.id}
                      />
                    ))}
                    {hiddenOperationCount > 0 && (
                      <div className="phlo-v2-noise-row">
                        {hiddenOperationCount} older operations kept out of the
                        DOM. Use target selection to narrow the working set.
                      </div>
                    )}
                  </div>
                </>
              )}
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

        {!selectedIsWap && (
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
                    value={formatDateTime(latest.completed_at)}
                  />
                </dl>
                <div className="phlo-v2-action-row">
                  {(detail.data?.actions ?? []).map((action) => (
                    <ActionButton
                      action={action}
                      key={action.id}
                      onRun={(actionId) => {
                        void runV2Action({ data: { actionId } }).then(
                          (next) => {
                            const operation = next.data?.operation
                            if (operation) {
                              setLocalOperations((current) =>
                                mergeOperations([operation], current),
                              )
                            }
                            invalidateCachedResources(['v2:operations'])
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
                {actionMessage && (
                  <div className="phlo-v2-panel-footer">{actionMessage}</div>
                )}
                {selectedFailure && (
                  <div className="phlo-v2-detail-list">
                    <div className="phlo-v2-mini-row" data-state="error">
                      <span>{selectedFailure.title}</span>
                      <small>{selectedFailure.message}</small>
                    </div>
                  </div>
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
                <p>
                  There are no Phlo operation records for this lakehouse yet.
                </p>
              </>
            )}
            {detail.error && (
              <div className="phlo-v2-panel-footer">{detail.error}</div>
            )}
            {result.error && (
              <div className="phlo-v2-panel-footer">{result.error}</div>
            )}
          </aside>
        )}
      </section>
    </V2Page>
  )
}

function WapOperationFocus({ operation }: { operation: V2Operation }) {
  const metadata = operation.metadata
  const tables = wapTables(operation)
  const flow = wapOperationFlow(operation, tables)
  const branch = textMetric(metadata, 'branch') ?? operation.target?.label
  const fields = [
    ['Run', textMetric(metadata, 'run_id') ?? operation.id],
    ['Branch', branch],
    ['Source hash', textMetric(metadata, 'source_hash')],
    ['Target before', textMetric(metadata, 'target_hash_before')],
    ['Target after', textMetric(metadata, 'target_hash_after')],
    ['Completed', formatDateTime(operation.completed_at)],
  ].filter((field): field is [string, string] => Boolean(field[1]))

  return (
    <div className="phlo-v2-wap-operation">
      <div className="phlo-v2-wap-operation-header">
        <div>
          <span className="phlo-v2-inspector-label">WAP execution</span>
          <strong>Execution report</strong>
          <p>
            {operation.status} · {branch ?? 'branch unknown'} · {tables.length}{' '}
            table{tables.length === 1 ? '' : 's'}
          </p>
        </div>
        <span className="phlo-v2-pill">{operation.status}</span>
      </div>
      <dl className="phlo-v2-wap-operation-fields">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <div className="phlo-v2-wap-operation-evidence">
        <div className="phlo-v2-wap-operation-steps">
          <div>
            <span>Branch</span>
            <strong>{branch ?? 'branch unknown'}</strong>
            <small>
              {textMetric(metadata, 'source_hash') ?? 'source unknown'}
            </small>
          </div>
          <div>
            <span>Table</span>
            <strong>{tables[0]?.name ?? 'table refs missing'}</strong>
            <small>
              {tables[0]?.records
                ? `${tables[0].records} rows`
                : 'records unknown'}
            </small>
          </div>
          <div>
            <span>Publish</span>
            <strong>{operation.name}</strong>
            <small>
              {textMetric(metadata, 'target_hash_after') ?? 'target unknown'}
            </small>
          </div>
        </div>
        <div className="phlo-v2-wap-operation-flow">
          <V2FlowCanvas edges={flow.edges} nodes={flow.nodes} />
        </div>
        <div className="phlo-v2-wap-operation-tables">
          <div className="phlo-v2-workspace-toolbar">
            <span>Affected tables</span>
            <span className="phlo-v2-pill">{tables.length}</span>
          </div>
          {tables.map((table) => (
            <div className="phlo-v2-mini-row" key={table.id}>
              <span>
                <Database className="size-3.5" />
                {table.name}
              </span>
              <small>
                {[
                  table.namespace,
                  table.format,
                  table.records ? `${table.records} records` : null,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </small>
            </div>
          ))}
          {tables.length === 0 && (
            <p>
              Report has no table refs. Branch and hash evidence are still
              shown.
            </p>
          )}
        </div>
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
  const failure = operationFailure(operation)
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
          {formatDateTime(operation.completed_at) ?? 'in progress'}
        </div>
        {failure && (
          <div className="phlo-v2-row-meta phlo-v2-row-evidence">
            {failure.message}
          </div>
        )}
      </div>
      <span className="phlo-v2-pill">{operation.status}</span>
    </button>
  )
}

function mergeOperations(
  primary: Array<V2Operation>,
  secondary: Array<V2Operation>,
): Array<V2Operation> {
  const merged = new Map<string, V2Operation>()
  for (const operation of [...primary, ...secondary]) {
    merged.set(operation.id, operation)
  }
  return Array.from(merged.values()).sort((left, right) =>
    operationTimestamp(right).localeCompare(operationTimestamp(left)),
  )
}

function operationTimestamp(operation: V2Operation): string {
  return operation.completed_at ?? operation.started_at ?? operation.id
}

function wapTables(operation: V2Operation): Array<{
  id: string
  name: string
  namespace: string | null
  format: string | null
  records: string | null
}> {
  const rawTables = operation.metadata.tables
  if (!Array.isArray(rawTables)) return []
  return rawTables
    .map((item) => {
      if (typeof item === 'string') {
        const namespace = item.includes('.')
          ? item.split('.').slice(0, -1).join('.')
          : null
        return {
          id: item,
          name: item.split('.').at(-1) ?? item,
          namespace,
          format: null,
          records: null,
        }
      }
      if (!item || typeof item !== 'object') return null
      const table = item as Record<string, unknown>
      const metadata =
        table.metadata && typeof table.metadata === 'object'
          ? (table.metadata as Record<string, unknown>)
          : {}
      const id = String(table.id ?? table.asset_id ?? table.name ?? '')
      if (!id) return null
      const name = String(table.name ?? id.split('.').at(-1) ?? id)
      return {
        id,
        name,
        namespace: textValue(table.namespace ?? table.schema_name),
        format: textValue(table.format),
        records: textValue(metadata.records ?? table.records),
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
}

function wapOperationFlow(
  operation: V2Operation,
  tables: ReturnType<typeof wapTables>,
): { nodes: Array<V2FlowNode>; edges: Array<V2FlowEdge> } {
  const branch =
    textMetric(operation.metadata, 'branch') ??
    operation.target?.label ??
    'branch'
  const sourceHash = textMetric(operation.metadata, 'source_hash')
  const targetHash = textMetric(operation.metadata, 'target_hash_after')
  const tableNodes = tables.slice(0, 6).map(
    (table): V2FlowNode => ({
      id: `table:${table.id}`,
      kind: 'table',
      label: table.name,
      lane: 'table',
      metric: table.records ? `${table.records} rows` : undefined,
    }),
  )
  const nodes: Array<V2FlowNode> = [
    {
      id: 'branch',
      kind: 'branch',
      label: branch,
      lane: 'branch',
      metric: sourceHash ?? undefined,
    },
    ...tableNodes,
    {
      id: 'publish',
      kind: 'operation',
      label: operation.name,
      lane: 'publish',
      metric: targetHash ?? undefined,
    },
  ]
  const edges: Array<V2FlowEdge> =
    tableNodes.length > 0
      ? [
          ...tableNodes.map((table) => ({
            id: `branch:${table.id}`,
            source: 'branch',
            target: table.id,
            label: 'writes',
          })),
          ...tableNodes.map((table) => ({
            id: `${table.id}:publish`,
            source: table.id,
            target: 'publish',
            label: 'promotes',
          })),
        ]
      : [
          {
            id: 'branch:publish',
            source: 'branch',
            target: 'publish',
            label: 'promotes',
          },
        ]
  return { edges, nodes }
}

function buildOperationLedger(operations: Array<V2Operation>) {
  const groups = new Map<
    string,
    {
      id: string
      kind: string
      label: string
      operations: Array<V2Operation>
    }
  >()

  for (const operation of operations) {
    const target = operation.target
    const id = target?.id ?? operation.kind
    const existing = groups.get(id)
    if (existing) {
      existing.operations.push(operation)
      continue
    }
    groups.set(id, {
      id,
      kind: target?.kind ?? operation.kind,
      label: target?.label ?? operation.kind,
      operations: [operation],
    })
  }

  return Array.from(groups.values())
    .map((group) => {
      const sorted = group.operations
        .slice()
        .sort((left, right) =>
          operationTimestamp(right).localeCompare(operationTimestamp(left)),
        )
      const failed = sorted.filter(
        (operation) => operation.status === 'failed',
      ).length
      const succeeded = sorted.filter(
        (operation) => operation.status === 'succeeded',
      ).length
      return {
        id: group.id,
        kind: group.kind,
        label: group.label,
        latest: sorted[0],
        failed,
        succeeded,
        lastSeen: operationTimestamp(sorted[0]) || 'pending',
        state: failed > 0 ? 'error' : (sorted[0]?.health.state ?? 'unknown'),
      }
    })
    .slice(0, 8)
}

function operationFailure(
  operation: V2Operation,
): { title: string; message: string } | null {
  if (operation.status !== 'failed' && operation.health.state !== 'error') {
    return null
  }
  const exceptionType = textMetric(operation.metadata, 'exception_type')
  const message =
    firstTextMetric(operation.metadata, [
      'exception_message',
      'failure_reason',
      'error',
      'reason',
      'message',
    ]) ??
    operation.health.message ??
    'No failure message recorded.'

  return {
    title: exceptionType ? `${exceptionType} failure` : 'Failure reason',
    message,
  }
}

function operationMetadata(
  operation: V2Operation,
): Array<[string, NonNullable<unknown>]> {
  const keys = [
    'pipeline_step',
    'source',
    'file_count',
    'package_path',
    'exception_type',
    'exception_message',
  ]
  return keys
    .map((key) => [key, operation.metadata[key]] as const)
    .filter((entry): entry is [string, NonNullable<unknown>] =>
      Boolean(entry[1]),
    )
    .slice(0, 6)
}

function firstTextMetric(
  metadata: Record<string, NonNullable<unknown>>,
  keys: Array<string>,
): string | null {
  for (const key of keys) {
    const value = textMetric(metadata, key)
    if (value) return value
  }
  return null
}

function textMetric(
  metadata: Record<string, NonNullable<unknown>>,
  key: string,
): string | null {
  const value = metadata[key]
  return typeof value === 'string' && value.trim() ? value : null
}

function textValue(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) return value
  if (typeof value === 'number') return String(value)
  return null
}

function formatDateTime(value?: string | null): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'UTC',
  }).format(date)} UTC`
}

function humanizeKey(key: string): string {
  return key.replaceAll('_', ' ')
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

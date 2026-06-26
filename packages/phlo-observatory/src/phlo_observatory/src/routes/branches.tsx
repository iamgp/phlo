import { createFileRoute } from '@tanstack/react-router'
import {
  AlertTriangle,
  Database,
  GitBranch,
  GitCompare,
  History,
  Plus,
  Table2,
} from 'lucide-react'
import { useEffect, useReducer } from 'react'
import type { ReactNode } from 'react'

import type {
  V2Branch,
  V2BranchDetail,
  V2Operation,
  V2ResourceResult,
  V2Table,
} from '@/v2/api/types'
import type { V2FlowEdge, V2FlowNode } from '@/v2/components/V2FlowCanvas'
import {
  getV2BranchDetailDirect,
  getV2BranchRecords,
  getV2OperationRecords,
  runV2BranchAction,
} from '@/v2/api/resources'
import { V2FlowCanvas } from '@/v2/components/V2FlowCanvas'
import { V2Page } from '@/v2/components/V2Page'
import {
  invalidateCachedResources,
  useLiveResource,
} from '@/v2/routes/liveResource'

export const Route = createFileRoute('/branches')({
  component: Branches,
})

type BranchesState = {
  actionMessage: string | null
  activePanel: BranchPanel
  createdBranches: Array<V2Branch>
  detail: V2ResourceResult<V2BranchDetail>
  selectedId: string | null
}

type BranchesAction =
  | { type: 'actionMessage'; message: string | null }
  | { type: 'activePanel'; panel: BranchPanel }
  | { type: 'detail'; detail: V2ResourceResult<V2BranchDetail> }
  | { type: 'select'; selectedId: string | null }
  | { type: 'branchCreated'; branch: V2Branch; message: string | null }

function branchesReducer(
  state: BranchesState,
  action: BranchesAction,
): BranchesState {
  switch (action.type) {
    case 'actionMessage':
      return { ...state, actionMessage: action.message }
    case 'activePanel':
      return { ...state, activePanel: action.panel }
    case 'detail':
      return { ...state, detail: action.detail }
    case 'select':
      return { ...state, selectedId: action.selectedId }
    case 'branchCreated':
      return {
        ...state,
        actionMessage: action.message,
        createdBranches: mergeBranches(state.createdBranches, [action.branch]),
        selectedId: action.branch.id,
      }
  }
}

export function Branches() {
  const result = useLiveResource(getV2BranchRecords, 60_000, 'v2:branches')
  const operationsResult = useLiveResource(
    getV2OperationRecords,
    60_000,
    'v2:operations',
  )
  const [
    { actionMessage, activePanel, createdBranches, detail, selectedId },
    dispatch,
  ] = useReducer(branchesReducer, {
    actionMessage: null,
    activePanel: 'compare',
    createdBranches: [],
    detail: {
      data: null,
      error: null,
    },
    selectedId: null,
  })
  const branches = mergeBranches(createdBranches, result.data ?? [])
  const selected =
    branches.find((branch) => branch.id === selectedId) ??
    branches.find((branch) => branch.current) ??
    branches[0]
  const selectedCompare = detail.data?.compare ?? branchCompare(selected)
  const selectedTableCount =
    detail.data?.tables.length ?? metadataNumber(selected, 'tables')
  const branchOperations = branchRelatedOperations(
    selected,
    operationsResult.data ?? [],
  )
  const selectedEvidenceCount = mergeOperations(
    branchOperations,
    detail.data?.commits ?? [],
  ).length

  useEffect(() => {
    const branchId = selected?.id
    if (!branchId) {
      dispatch({ type: 'detail', detail: { data: null, error: null } })
      return
    }
    let cancelled = false
    dispatch({ type: 'detail', detail: { data: null, error: null } })
    void getV2BranchDetailDirect({ branchName: branchId }).then((next) => {
      if (!cancelled) dispatch({ type: 'detail', detail: next })
    })
    return () => {
      cancelled = true
    }
  }, [selected?.id])

  return (
    <V2Page
      kicker="Changes"
      title="Catalog changes"
      description="Review branch state, table drift, and guarded change workflows."
      action={<span className="phlo-v2-pill">{branches.length} branches</span>}
    >
      <section className="phlo-v2-surface-grid phlo-v2-branch-grid">
        <div className="phlo-v2-branch-main">
          <div className="phlo-v2-list-surface">
            <div className="phlo-v2-browser-toolbar">
              <span>
                <GitBranch className="size-4" />
                Branches
              </span>
              <button
                onClick={() => {
                  const branchName = window.prompt('New branch name')
                  if (!branchName) return
                  if (
                    !window.confirm(
                      `Create branch ${branchName}? This writes Observatory branch state through phlo-api.`,
                    )
                  ) {
                    return
                  }
                  void runV2BranchAction({
                    data: { actionId: `branch:create:${branchName}` },
                  }).then((next) => {
                    invalidateCachedResources(['v2:operations', 'v2:branches'])
                    const message =
                      next.data?.message ??
                      next.error ??
                      'Branch action completed'
                    if (next.data?.status === 'succeeded') {
                      dispatch({
                        type: 'branchCreated',
                        branch: {
                          current: false,
                          id: branchName,
                          metadata: { source: 'local' },
                          name: branchName,
                          protected: false,
                        },
                        message,
                      })
                    } else {
                      dispatch({ type: 'actionMessage', message })
                    }
                  })
                }}
                type="button"
              >
                <Plus className="size-3.5" />
                Branch
              </button>
            </div>
            {branches.map((branch) => (
              <button
                className="phlo-v2-row phlo-v2-select-row"
                data-active={branch.id === selected?.id}
                key={branch.id}
                onClick={() =>
                  dispatch({ type: 'select', selectedId: branch.id })
                }
                type="button"
              >
                <div className="phlo-v2-row-main">
                  <div className="phlo-v2-row-title">{branch.name}</div>
                  <div className="phlo-v2-row-meta">
                    {branch.current ? 'Current branch' : 'Review branch'}
                    {branchDelta(branch) && <> · {branchDelta(branch)}</>}
                  </div>
                </div>
                <span className="phlo-v2-pill">
                  {branch.current
                    ? 'current'
                    : branch.protected
                      ? 'protected'
                      : 'branch'}
                </span>
              </button>
            ))}
          </div>
          {selected && (
            <>
              <section className="phlo-v2-branch-summary">
                <div className="phlo-v2-branch-summary-copy">
                  <div className="phlo-v2-inspector-label">Selected branch</div>
                  <h2>{selected.name}</h2>
                  <p>
                    {detail.data
                      ? branchNarrative(detail.data)
                      : branchNarrativeFromBranch(selected)}
                  </p>
                </div>
                <div className="phlo-v2-action-row">
                  <button
                    data-active={activePanel === 'compare'}
                    onClick={() =>
                      dispatch({ type: 'activePanel', panel: 'compare' })
                    }
                    type="button"
                  >
                    <GitCompare className="size-3.5" />
                    Compare
                  </button>
                  <button
                    data-active={activePanel === 'history'}
                    onClick={() =>
                      dispatch({ type: 'activePanel', panel: 'history' })
                    }
                    type="button"
                  >
                    <History className="size-3.5" />
                    History
                  </button>
                  <button
                    data-active={activePanel === 'contents'}
                    onClick={() =>
                      dispatch({ type: 'activePanel', panel: 'contents' })
                    }
                    type="button"
                  >
                    <Table2 className="size-3.5" />
                    Contents
                  </button>
                </div>
                <dl className="phlo-v2-branch-facts">
                  <div>
                    <dt>Tables</dt>
                    <dd>{selectedTableCount}</dd>
                  </div>
                  <div>
                    <dt>Evidence</dt>
                    <dd>{selectedEvidenceCount}</dd>
                  </div>
                  <div>
                    <dt>Added</dt>
                    <dd>{selectedCompare.added ?? 0}</dd>
                  </div>
                  <div>
                    <dt>Changed</dt>
                    <dd>{selectedCompare.changed ?? 0}</dd>
                  </div>
                  <div>
                    <dt>Ahead / behind</dt>
                    <dd>
                      {selectedCompare.ahead ?? 0} /{' '}
                      {selectedCompare.behind ?? 0}
                    </dd>
                  </div>
                  <div>
                    <dt>Protected</dt>
                    <dd>{selected.protected ? 'yes' : 'no'}</dd>
                  </div>
                </dl>
              </section>
              <WapReport operations={branchOperations} />
              {detail.data ? (
                <BranchPanelView
                  active={activePanel}
                  detail={detail.data}
                  operations={branchOperations}
                />
              ) : (
                <BranchPanelFallback
                  active={activePanel}
                  branch={selected}
                  operations={branchOperations}
                />
              )}
            </>
          )}
          {detail.error && (
            <div className="phlo-v2-panel-footer">{detail.error}</div>
          )}
          {actionMessage && (
            <div className="phlo-v2-panel-footer">{actionMessage}</div>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
          {operationsResult.error && (
            <div className="phlo-v2-panel-footer">{operationsResult.error}</div>
          )}
        </div>
      </section>
    </V2Page>
  )
}

type BranchPanel = 'contents' | 'compare' | 'history'

function mergeBranches(
  left: Array<V2Branch>,
  right: Array<V2Branch>,
): Array<V2Branch> {
  const merged = new Map<string, V2Branch>()
  for (const branch of [...left, ...right]) {
    merged.set(branch.id, branch)
  }
  return Array.from(merged.values())
}

function mergeOperations(
  left: Array<V2Operation>,
  right: Array<V2Operation>,
): Array<V2Operation> {
  const merged = new Map<string, V2Operation>()
  for (const operation of [...left, ...right]) {
    merged.set(operation.id, operation)
  }
  return Array.from(merged.values())
}

function branchRelatedOperations(
  branch: V2Branch | undefined,
  operations: Array<V2Operation>,
): Array<V2Operation> {
  if (!branch) return []
  return operations.filter((operation) => {
    const metadataBranch = metadataString(operation.metadata, 'branch')
    return (
      operation.target?.kind === 'branch' &&
      (operation.target.id === branch.id ||
        operation.target.id === branch.name ||
        metadataBranch === branch.id ||
        metadataBranch === branch.name)
    )
  })
}

function BranchPanelView({
  active,
  detail,
  operations,
}: {
  active: BranchPanel
  detail: V2BranchDetail
  operations: Array<V2Operation>
}) {
  if (active === 'compare') {
    return (
      <div className="phlo-v2-branch-review">
        <div className="phlo-v2-command-strip">
          <BranchMetric
            icon={<Plus className="size-4" />}
            label="Added"
            value={detail.compare.added ?? 0}
          />
          <BranchMetric
            icon={<GitCompare className="size-4" />}
            label="Changed"
            value={detail.compare.changed ?? 0}
          />
          <BranchMetric
            icon={<AlertTriangle className="size-4" />}
            label="Removed"
            value={detail.compare.removed ?? 0}
          />
        </div>
        <BranchReviewEvidence
          branch={detail.branch}
          operations={operations}
          tables={detail.tables}
        />
      </div>
    )
  }

  if (active === 'history') {
    const commits = mergeOperations(operations, detail.commits)
    return (
      <div className="phlo-v2-detail-list">
        {commits.length > 0 ? (
          commits
            .slice(0, 8)
            .map((commit) => <CommitRow commit={commit} key={commit.id} />)
        ) : (
          <p>No operation evidence returned for this branch yet.</p>
        )}
      </div>
    )
  }

  return (
    <div className="phlo-v2-detail-list">
      {detail.tables.slice(0, 8).map((table) => (
        <TableRow key={table.id} table={table} />
      ))}
      {detail.tables.length === 0 && <p>No branch contents returned yet.</p>}
    </div>
  )
}

function BranchPanelFallback({
  active,
  branch,
  operations,
}: {
  active: BranchPanel
  branch: V2Branch
  operations: Array<V2Operation>
}) {
  if (active === 'compare') {
    const compare = branchCompare(branch)
    return (
      <div className="phlo-v2-branch-review">
        <div className="phlo-v2-command-strip">
          <BranchMetric
            icon={<Plus className="size-4" />}
            label="Added"
            value={compare.added ?? 0}
          />
          <BranchMetric
            icon={<GitCompare className="size-4" />}
            label="Changed"
            value={compare.changed ?? 0}
          />
          <BranchMetric
            icon={<AlertTriangle className="size-4" />}
            label="Removed"
            value={compare.removed ?? 0}
          />
        </div>
        <BranchReviewEvidence
          branch={branch}
          operations={operations}
          tables={[]}
        />
      </div>
    )
  }

  if (active === 'history' && operations.length > 0) {
    return (
      <div className="phlo-v2-detail-list">
        {operations.slice(0, 8).map((operation) => (
          <CommitRow commit={operation} key={operation.id} />
        ))}
      </div>
    )
  }

  return (
    <div className="phlo-v2-detail-list">
      <p>
        No branch contents returned by the API yet. WAP evidence is shown above.
      </p>
    </div>
  )
}

function WapReport({ operations }: { operations: Array<V2Operation> }) {
  const report = operations.find((operation) => operation.kind === 'wap')
  if (!report) return null
  const metadata = report.metadata
  const fields = [
    ['Run', metadataString(metadata, 'run_id') ?? report.id],
    ['Branch', metadataString(metadata, 'branch') ?? report.target?.id],
    ['Source hash', metadataString(metadata, 'source_hash')],
    ['Target before', metadataString(metadata, 'target_hash_before')],
    ['Target after', metadataString(metadata, 'target_hash_after')],
    ['WAP branch deleted', metadataBoolean(metadata, 'source_deleted')],
  ].filter((field): field is [string, string] => Boolean(field[1]))

  return (
    <section className="phlo-v2-wap-report">
      <div className="phlo-v2-inspector-label">WAP report</div>
      <h3>{report.name}</h3>
      <p>
        {[report.status, formatDateTime(report.completed_at)]
          .filter(Boolean)
          .join(' · ')}
      </p>
      <dl>
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function BranchMetric({
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

function BranchReviewEvidence({
  branch,
  operations,
  tables,
}: {
  branch: V2Branch
  operations: Array<V2Operation>
  tables: Array<V2Table>
}) {
  const flow = branchFlow(branch, operations, tables)
  return (
    <div className="phlo-v2-branch-evidence">
      <div className="phlo-v2-branch-flow">
        <V2FlowCanvas edges={flow.edges} nodes={flow.nodes} />
      </div>
      <div className="phlo-v2-branch-table-list">
        {tables.length > 0 ? (
          tables
            .slice(0, 8)
            .map((table) => <TableRow key={table.id} table={table} />)
        ) : (
          <p>
            WAP reported a changed table count, but the report did not include
            table refs.
          </p>
        )}
      </div>
    </div>
  )
}

function branchFlow(
  branch: V2Branch,
  operations: Array<V2Operation>,
  tables: Array<V2Table>,
): { nodes: Array<V2FlowNode>; edges: Array<V2FlowEdge> } {
  const report = operations.find((operation) => operation.kind === 'wap')
  const sourceHash = metadataString(report?.metadata ?? {}, 'source_hash')
  const targetHash = metadataString(report?.metadata ?? {}, 'target_hash_after')
  const tableNodes = tables.slice(0, 6).map(
    (table): V2FlowNode => ({
      id: `table:${table.id}`,
      kind: 'table',
      label: table.name,
      lane: 'table',
      metric:
        tableRecordCount(table) === 'n/a'
          ? undefined
          : `${tableRecordCount(table)} rows`,
      subtitle: table.namespace ?? undefined,
    }),
  )
  const nodes: Array<V2FlowNode> = [
    {
      id: 'branch',
      kind: 'branch',
      label: branch.name,
      lane: 'branch',
      metric: sourceHash ?? undefined,
    },
    ...tableNodes,
    {
      id: 'publish',
      kind: 'operation',
      label: report?.name ?? 'WAP publish',
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

function TableRow({ table }: { table: V2Table }) {
  return (
    <div className="phlo-v2-mini-row">
      <span>
        <Database className="size-3.5" />
        {table.name}
      </span>
      <small>
        {[table.namespace, table.format, `${tableRecordCount(table)} records`]
          .filter(Boolean)
          .join(' · ')}
      </small>
    </div>
  )
}

function CommitRow({ commit }: { commit: V2Operation }) {
  const reason = operationReason(commit)
  const sourceHash = metadataString(commit.metadata, 'source_hash')
  const targetHash = metadataString(commit.metadata, 'target_hash_after')
  const hashMovement =
    sourceHash && targetHash ? `${sourceHash} -> ${targetHash}` : null
  return (
    <div
      className={`phlo-v2-mini-row${
        commit.kind === 'wap' ? ' phlo-v2-wap-history-row' : ''
      }`}
    >
      <span>{commit.name}</span>
      <small>
        {[
          commit.status,
          formatDateTime(commit.completed_at),
          hashMovement,
          reason,
        ]
          .filter(Boolean)
          .join(' · ')}
      </small>
    </div>
  )
}

function branchNarrative(detail: V2BranchDetail): string {
  const changed = detail.compare.changed ?? 0
  const added = detail.compare.added ?? 0
  const removed = detail.compare.removed ?? 0
  const direction =
    detail.branch.current || detail.branch.protected
      ? 'Protected baseline'
      : 'Review candidate'
  return `${direction}: ${detail.tables.length} tables, ${changed} changed, ${added} added, ${removed} removed.`
}

function branchNarrativeFromBranch(branch: V2Branch): string {
  const compare = branchCompare(branch)
  const direction =
    branch.current || branch.protected
      ? 'Protected baseline'
      : 'Review candidate'
  return `${direction}: ${metadataNumber(branch, 'tables')} tables, ${compare.changed ?? 0} changed, ${compare.added ?? 0} added, ${compare.removed ?? 0} removed.`
}

function branchDelta(branch: V2Branch): string | null {
  const ahead = metadataNumber(branch, 'ahead')
  const behind = metadataNumber(branch, 'behind')
  const changed = metadataNumber(branch, 'changed')
  if (ahead || behind) return `${ahead} ahead / ${behind} behind`
  if (changed) return `${changed} changed`
  return null
}

function branchCompare(branch?: V2Branch): Record<string, number> {
  if (!branch) return {}
  return {
    added: metadataNumber(branch, 'added'),
    changed: metadataNumber(branch, 'changed'),
    removed: metadataNumber(branch, 'removed'),
    ahead: metadataNumber(branch, 'ahead'),
    behind: metadataNumber(branch, 'behind'),
  }
}

function tableRecordCount(table: V2Table): string {
  const records = table.metadata.records
  if (typeof records === 'number' || typeof records === 'string') {
    return String(records)
  }
  return 'n/a'
}

function metadataNumber(item: V2Branch | undefined, key: string): number {
  if (!item) return 0
  const value = item.metadata[key]
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const parsed = Number.parseInt(value, 10)
    return Number.isNaN(parsed) ? 0 : parsed
  }
  return 0
}

function metadataString(
  metadata: Record<string, unknown>,
  key: string,
): string | null {
  const value = metadata[key]
  if (typeof value === 'string' && value.length > 0) return value
  if (typeof value === 'number') return String(value)
  return null
}

function metadataBoolean(
  metadata: Record<string, unknown>,
  key: string,
): string | null {
  const value = metadata[key]
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  if (typeof value === 'string' && value.length > 0) return value
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

function operationReason(operation: V2Operation): string | null {
  const reason = operation.metadata.failure_reason ?? operation.health.message
  return typeof reason === 'string' && reason ? reason : null
}

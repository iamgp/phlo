import { createFileRoute } from '@tanstack/react-router'
import { GitBranch, GitCompare, History, Plus, Table2 } from 'lucide-react'
import { useEffect, useReducer } from 'react'

import type {
  V2BranchDetail,
  V2ResourceItem,
  V2ResourceResult,
} from '@/v2/api/types'
import {
  getV2BranchDetail,
  getV2Branches,
  runV2BranchAction,
} from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import {
  invalidateCachedResources,
  useLiveResource,
} from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/branches')({
  component: Branches,
})

type BranchesState = {
  actionMessage: string | null
  activePanel: BranchPanel
  createdBranches: Array<V2ResourceItem>
  detail: V2ResourceResult<V2BranchDetail>
  selectedId: string | null
}

type BranchesAction =
  | { type: 'actionMessage'; message: string | null }
  | { type: 'activePanel'; panel: BranchPanel }
  | { type: 'detail'; detail: V2ResourceResult<V2BranchDetail> }
  | { type: 'select'; selectedId: string | null }
  | { type: 'branchCreated'; branch: V2ResourceItem; message: string | null }

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
  const result = useLiveResource(getV2Branches, 60_000, 'v2:branches')
  const [
    { actionMessage, activePanel, createdBranches, detail, selectedId },
    dispatch,
  ] = useReducer(branchesReducer, {
    actionMessage: null,
    activePanel: 'contents',
    createdBranches: [],
    detail: {
      data: null,
      error: null,
    },
    selectedId: null,
  })
  const branches = mergeBranches(result.data ?? [], createdBranches)
  const selected =
    branches.find((branch) => branch.id === selectedId) ??
    branches.find((branch) => branch.status === 'current') ??
    branches[0]

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getV2BranchDetail({ data: { branchName: selected.id } }).then(
      (next) => {
        if (!cancelled) dispatch({ type: 'detail', detail: next })
      },
    )
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <V2Page
      kicker="Changes"
      title="Catalog changes"
      description="Review branch state, table drift, and guarded change workflows."
      action={<span className="phlo-v2-pill">{branches.length} branches</span>}
    >
      <section className="phlo-v2-surface-grid">
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
                        id: branchName,
                        kind: 'branch',
                        metadata: { source: 'local' },
                        name: branchName,
                        status: 'branch',
                        summary: 'Local Observatory branch state',
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
                  {branch.summary ?? branch.kind}
                </div>
              </div>
              <span className="phlo-v2-pill">
                {branch.status ?? branch.kind}
              </span>
            </button>
          ))}
        </div>
        <aside className="phlo-v2-inspector">
          <div className="phlo-v2-inspector-label">Change controls</div>
          <h2>{selected?.name ?? 'No branch selected'}</h2>
          <p>
            Branch state, compare summary, and commit history for the selected
            catalog branch.
          </p>
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
          {detail.data && (
            <>
              <dl className="phlo-v2-facts">
                <dt>Contents</dt>
                <dd>{detail.data.contents.length}</dd>
                <dt>Commits</dt>
                <dd>{detail.data.commits.length}</dd>
                <dt>Added</dt>
                <dd>{detail.data.compare.added ?? 0}</dd>
                <dt>Changed</dt>
                <dd>{detail.data.compare.changed ?? 0}</dd>
              </dl>
              <BranchPanelView active={activePanel} detail={detail.data} />
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
        </aside>
      </section>
    </V2Page>
  )
}

type BranchPanel = 'contents' | 'compare' | 'history'

function mergeBranches(
  left: Array<V2ResourceItem>,
  right: Array<V2ResourceItem>,
): Array<V2ResourceItem> {
  const merged = new Map<string, V2ResourceItem>()
  for (const branch of [...left, ...right]) {
    merged.set(branch.id, branch)
  }
  return Array.from(merged.values())
}

function BranchPanelView({
  active,
  detail,
}: {
  active: BranchPanel
  detail: V2BranchDetail
}) {
  if (active === 'compare') {
    return (
      <div className="phlo-v2-detail-list">
        {(['added', 'changed', 'removed'] as const).map((key) => (
          <div className="phlo-v2-mini-row" key={key}>
            <span>{key}</span>
            <small>{detail.compare[key] ?? 0}</small>
          </div>
        ))}
      </div>
    )
  }

  if (active === 'history') {
    return (
      <div className="phlo-v2-detail-list">
        {detail.commits.length > 0 ? (
          detail.commits.slice(0, 8).map((commit) => (
            <div className="phlo-v2-mini-row" key={commit.id}>
              <span>{commit.name}</span>
              <small>
                {[commit.status, commit.completed_at]
                  .filter(Boolean)
                  .join(' · ')}
              </small>
            </div>
          ))
        ) : (
          <p>No commit history returned yet.</p>
        )}
      </div>
    )
  }

  return (
    <div className="phlo-v2-detail-list">
      {detail.contents.slice(0, 8).map((entry) => (
        <div className="phlo-v2-mini-row" key={entry.id}>
          <span>{entry.label}</span>
          <small>{entry.kind}</small>
        </div>
      ))}
      {detail.contents.length === 0 && <p>No branch contents returned yet.</p>}
    </div>
  )
}

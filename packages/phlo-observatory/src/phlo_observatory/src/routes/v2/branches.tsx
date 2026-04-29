import { createFileRoute } from '@tanstack/react-router'
import { GitBranch, GitCompare, History, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'

import type { V2BranchDetail, V2ResourceResult } from '@/v2/api/types'
import { getV2BranchDetail, getV2Branches } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/branches')({
  component: Branches,
})

function Branches() {
  const result = useLiveResource(getV2Branches)
  const branches = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    branches.find((branch) => branch.id === selectedId) ??
    branches.find((branch) => branch.status === 'current') ??
    branches[0]
  const [detail, setDetail] = useState<V2ResourceResult<V2BranchDetail>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getV2BranchDetail({ data: { branchName: selected.id } }).then(
      (next) => {
        if (!cancelled) setDetail(next)
      },
    )
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <V2Page
      kicker="Branches"
      title="Catalog branches"
      description="Review branch state and prepare guarded change workflows."
      action={<span className="phlo-v2-pill">{branches.length} branches</span>}
    >
      <section className="phlo-v2-surface-grid">
        <div className="phlo-v2-list-surface">
          <div className="phlo-v2-browser-toolbar">
            <span>
              <GitBranch className="size-4" />
              Branches
            </span>
            <button className="phlo-v2-icon-command" type="button">
              <Plus className="size-3.5" />
            </button>
          </div>
          {branches.map((branch) => (
            <button
              className="phlo-v2-row phlo-v2-select-row"
              data-active={branch.id === selected?.id}
              key={branch.id}
              onClick={() => setSelectedId(branch.id)}
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
            Compare, merge, and delete flows stay guarded behind phlo-api
            operations.
          </p>
          <div className="phlo-v2-action-row">
            <button type="button">
              <GitCompare className="size-3.5" />
              Compare
            </button>
            <button type="button">
              <History className="size-3.5" />
              History
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
              <div className="phlo-v2-detail-list">
                {detail.data.contents.slice(0, 6).map((entry) => (
                  <div className="phlo-v2-mini-row" key={entry.id}>
                    <span>{entry.label}</span>
                    <small>{entry.kind}</small>
                  </div>
                ))}
                {detail.data.contents.length === 0 && (
                  <p>No branch contents returned yet.</p>
                )}
              </div>
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

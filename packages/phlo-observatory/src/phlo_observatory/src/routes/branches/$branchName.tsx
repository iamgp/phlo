import { createFileRoute } from '@tanstack/react-router'
import { GitBranch, GitCommitHorizontal, Table2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryBranchDetail,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import { getObservatoryBranchDetail } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'

export const Route = createFileRoute('/branches/$branchName')({
  component: BranchDetailRoute,
})

function BranchDetailRoute() {
  const { branchName } = Route.useParams()
  return <BranchDetailView branchName={branchName} />
}

export function BranchDetailView({ branchName }: { branchName: string }) {
  const [result, setResult] = useState<
    ObservatoryResourceResult<ObservatoryBranchDetail>
  >({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getObservatoryBranchDetail({ data: { branchName } })
      .then(setResult)
      .catch(() =>
        setResult({
          data: null,
          error: 'Branch detail is unavailable.',
        }),
      )
  }, [branchName])

  const detail = result.data

  return (
    <ObservatoryPage
      action={
        <span className="phlo-observatory-pill">
          {detail?.branch.current ? 'current' : 'branch'}
        </span>
      }
      description="Branch contents, commits, and change impact."
      kicker="Branch"
      title={detail?.branch.name ?? branchName}
    >
      {detail ? (
        <section className="phlo-observatory-surface-grid">
          <div className="phlo-observatory-list-surface">
            <div className="phlo-observatory-browser-toolbar">
              <span>
                <Table2 className="size-4" />
                Contents
              </span>
              <span className="phlo-observatory-pill">
                {detail.contents.length} entries
              </span>
            </div>
            <div className="phlo-observatory-detail-list phlo-observatory-detail-list-padded">
              {detail.contents.map((entry) => (
                <div className="phlo-observatory-mini-row" key={entry.id}>
                  <span>{entry.label}</span>
                  <small>{entry.kind}</small>
                </div>
              ))}
              {detail.contents.length === 0 && (
                <p>No branch contents returned yet.</p>
              )}
            </div>
          </div>
          <aside className="phlo-observatory-inspector">
            <div className="phlo-observatory-inspector-label">
              Change impact
            </div>
            <h2>{detail.branch.name}</h2>
            <p>Branch state and compare summary.</p>
            <div className="phlo-observatory-detail-list">
              <Mini
                icon={<GitBranch className="size-3.5" />}
                label="Protected"
                value={detail.branch.protected ? 'yes' : 'no'}
              />
              <Mini
                icon={<GitCommitHorizontal className="size-3.5" />}
                label="Commits"
                value={String(detail.commits.length)}
              />
              <Mini label="Added" value={String(detail.compare.added ?? 0)} />
              <Mini
                label="Changed"
                value={String(detail.compare.changed ?? 0)}
              />
              <Mini
                label="Removed"
                value={String(detail.compare.removed ?? 0)}
              />
            </div>
          </aside>
        </section>
      ) : (
        <div className="phlo-observatory-empty-state">
          {result.error ?? 'Loading branch detail…'}
        </div>
      )}
    </ObservatoryPage>
  )
}

function Mini({
  icon,
  label,
  value,
}: {
  icon?: ReactNode
  label: string
  value: string
}) {
  return (
    <div className="phlo-observatory-mini-row">
      <span>
        {icon}
        {label}
      </span>
      <small>{value}</small>
    </div>
  )
}

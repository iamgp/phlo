import { createFileRoute } from '@tanstack/react-router'
import { Columns3, Database, GitBranch, Rows3 } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type { V2ResourceResult, V2TablePreview } from '@/v2/api/types'
import { getV2TablePreview } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'

export const Route = createFileRoute('/v2/data/$tableId')({
  component: TableDetailRoute,
})

function TableDetailRoute() {
  const { tableId } = Route.useParams()
  return <TableDetailView tableId={tableId} />
}

export function TableDetailView({ tableId }: { tableId: string }) {
  const [result, setResult] = useState<V2ResourceResult<V2TablePreview>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getV2TablePreview({ data: { tableId, limit: 50 } }).then(setResult)
  }, [tableId])

  const preview = result.data
  const table = preview?.table

  return (
    <V2Page
      action={<span className="phlo-v2-pill">{table?.branch ?? 'main'}</span>}
      description="Table detail, preview metadata, and row-journey entry point."
      kicker="Table"
      title={
        table?.namespace
          ? `${table.namespace}.${table.name}`
          : (table?.name ?? tableId)
      }
    >
      {preview && table ? (
        <section className="phlo-v2-surface-grid">
          <div className="phlo-v2-list-surface">
            <div className="phlo-v2-browser-toolbar">
              <span>
                <Columns3 className="size-4" />
                Columns
              </span>
              <span className="phlo-v2-pill">
                {preview.columns.length} columns
              </span>
            </div>
            <div className="phlo-v2-detail-list phlo-v2-detail-list-padded">
              {preview.columns.map((column) => (
                <div className="phlo-v2-mini-row" key={column}>
                  <span>{column}</span>
                  <small>column</small>
                </div>
              ))}
              {preview.columns.length === 0 && (
                <p>No column preview returned yet.</p>
              )}
            </div>
          </div>
          <aside className="phlo-v2-inspector">
            <div className="phlo-v2-inspector-label">Preview</div>
            <h2>{table.name}</h2>
            <p>{table.asset_id ?? 'No asset binding returned.'}</p>
            <div className="phlo-v2-detail-list">
              <Mini
                icon={<Rows3 className="size-3.5" />}
                label="Rows"
                value={String(preview.row_count ?? 'n/a')}
              />
              <Mini
                icon={<Database className="size-3.5" />}
                label="Format"
                value={table.format ?? 'unknown'}
              />
              <Mini
                icon={<GitBranch className="size-3.5" />}
                label="Branch"
                value={table.branch ?? 'main'}
              />
              <Mini
                label="Row journey"
                value="Waiting for stable row identity"
              />
            </div>
          </aside>
        </section>
      ) : (
        <div className="phlo-v2-empty-state">
          {result.error ?? 'Loading table detail...'}
        </div>
      )}
    </V2Page>
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
    <div className="phlo-v2-mini-row">
      <span>
        {icon}
        {label}
      </span>
      <small>{value}</small>
    </div>
  )
}

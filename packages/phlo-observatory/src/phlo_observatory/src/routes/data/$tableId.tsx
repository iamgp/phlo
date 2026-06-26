import { Link, createFileRoute } from '@tanstack/react-router'
import { Columns3, Database, GitBranch, Rows3 } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryResourceResult,
  ObservatoryRowJourney,
  ObservatoryTablePreview,
} from '@/observatory/api/types'
import {
  getObservatoryRowJourney,
  getObservatoryTablePreview,
} from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'

const previewLimit = 25

export const Route = createFileRoute('/data/$tableId')({
  component: TableDetailRoute,
})

function TableDetailRoute() {
  const { tableId } = Route.useParams()
  return <TableDetailView tableId={tableId} />
}

export function TableDetailView({ tableId }: { tableId: string }) {
  const [result, setResult] = useState<
    ObservatoryResourceResult<ObservatoryTablePreview>
  >({
    data: null,
    error: null,
  })
  const [journey, setJourney] = useState<
    ObservatoryResourceResult<ObservatoryRowJourney>
  >({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getObservatoryTablePreview({ data: { tableId, limit: previewLimit } })
      .then(setResult)
      .catch(() =>
        setResult({
          data: null,
          error: 'Table detail is unavailable.',
        }),
      )
  }, [tableId])

  const preview = result.data
  const table = preview?.table

  return (
    <ObservatoryPage
      action={
        <span className="phlo-observatory-pill">{table?.branch ?? 'main'}</span>
      }
      description="Table detail, preview metadata, and row-journey entry point."
      kicker="Table"
      title={
        table?.namespace
          ? `${table.namespace}.${table.name}`
          : (table?.name ?? tableId)
      }
    >
      {preview && table ? (
        <section className="phlo-observatory-surface-grid">
          <div className="phlo-observatory-list-surface">
            <div className="phlo-observatory-browser-toolbar">
              <span>
                <Columns3 className="size-4" />
                Preview rows
              </span>
              <span className="phlo-observatory-pill">
                {preview.columns.length} columns
              </span>
            </div>
            <div className="phlo-observatory-detail-list phlo-observatory-detail-list-padded">
              {preview.rows.slice(0, 8).map((row, index) => (
                <button
                  className="phlo-observatory-mini-row phlo-observatory-mini-row-stack"
                  key={String(row._phlo_row_id ?? index)}
                  onClick={() => {
                    const rowId = String(
                      row._phlo_row_id ?? `${table.id}:${index + 1}`,
                    )
                    void getObservatoryRowJourney({
                      data: { tableId: table.id, rowId },
                    }).then(setJourney)
                  }}
                  type="button"
                >
                  <span>{String(row._phlo_row_id ?? `row-${index + 1}`)}</span>
                  <small>
                    {Object.entries(row)
                      .filter(([key]) => key !== '_phlo_row_id')
                      .slice(0, 4)
                      .map(([key, value]) => `${key}: ${String(value)}`)
                      .join(' · ')}
                  </small>
                </button>
              ))}
              {preview.rows.length === 0 &&
                preview.columns.map((column) => (
                  <div className="phlo-observatory-mini-row" key={column}>
                    <span>{column}</span>
                    <small>column</small>
                  </div>
                ))}
              {journey.data && (
                <div className="phlo-observatory-detail-list">
                  <div className="phlo-observatory-mini-row">
                    <span>Selected row journey</span>
                    <small>{journey.data.row_id}</small>
                  </div>
                  <div className="phlo-observatory-mini-row">
                    <span>Upstream</span>
                    <small>
                      {journey.data.upstream
                        .map((item) => item.label)
                        .join(', ') || 'none'}
                    </small>
                  </div>
                  <div className="phlo-observatory-mini-row">
                    <span>Downstream</span>
                    <small>
                      {journey.data.downstream
                        .map((item) => item.label)
                        .join(', ') || 'none'}
                    </small>
                  </div>
                </div>
              )}
              {journey.error && (
                <div className="phlo-observatory-panel-footer">
                  {journey.error}
                </div>
              )}
              {preview.columns.length === 0 && (
                <p>No column preview returned yet.</p>
              )}
            </div>
          </div>
          <aside className="phlo-observatory-inspector">
            <div className="phlo-observatory-inspector-label">Preview</div>
            <h2>{table.name}</h2>
            <p>{table.asset_id ?? 'No asset binding returned.'}</p>
            <div className="phlo-observatory-detail-list">
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
                label="Preview rows"
                value={`${preview.rows.length} loaded${preview.has_more ? ' · more available' : ''}`}
              />
              <Mini label="Namespace" value={table.namespace ?? 'default'} />
              {table.asset_id && (
                <Link
                  className="phlo-observatory-mini-row"
                  to="/asset/$assetId"
                  params={{ assetId: table.asset_id }}
                >
                  <span>Open asset</span>
                  <small>{table.asset_id}</small>
                </Link>
              )}
            </div>
          </aside>
        </section>
      ) : (
        <div className="phlo-observatory-empty-state">
          {result.error
            ? 'Table detail is unavailable.'
            : 'Loading table detail…'}
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

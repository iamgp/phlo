import { Link, createFileRoute } from '@tanstack/react-router'
import { Columns3, Database, GitBranch, GitCompare, Rows3 } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2ResourceResult,
  V2RowJourney,
  V2StageDiff,
  V2TablePreview,
} from '@/v2/api/types'
import {
  getV2RowJourney,
  getV2StageDiff,
  getV2TablePreview,
} from '@/v2/api/resources'
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
  const [journey, setJourney] = useState<V2ResourceResult<V2RowJourney>>({
    data: null,
    error: null,
  })
  const [stageDiff, setStageDiff] = useState<V2ResourceResult<V2StageDiff>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getV2TablePreview({ data: { tableId, limit: 50 } }).then(setResult)
  }, [tableId])

  const preview = result.data
  const table = preview?.table
  const sourceTableId = table ? inferSourceTableId(table.id) : null

  useEffect(() => {
    if (!table || !sourceTableId || sourceTableId === table.id) return
    void getV2StageDiff({
      data: { sourceTableId, targetTableId: table.id },
    }).then(setStageDiff)
  }, [sourceTableId, table])

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
                Preview rows
              </span>
              <span className="phlo-v2-pill">
                {preview.columns.length} columns
              </span>
            </div>
            <div className="phlo-v2-detail-list phlo-v2-detail-list-padded">
              {preview.rows.slice(0, 8).map((row, index) => (
                <button
                  className="phlo-v2-mini-row phlo-v2-mini-row-stack"
                  key={String(row._phlo_row_id ?? index)}
                  onClick={() => {
                    const rowId = String(
                      row._phlo_row_id ?? `${table.id}:${index + 1}`,
                    )
                    void getV2RowJourney({
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
                  <div className="phlo-v2-mini-row" key={column}>
                    <span>{column}</span>
                    <small>column</small>
                  </div>
                ))}
              {journey.data && (
                <div className="phlo-v2-detail-list">
                  <div className="phlo-v2-mini-row">
                    <span>Selected row journey</span>
                    <small>{journey.data.row_id}</small>
                  </div>
                  <div className="phlo-v2-mini-row">
                    <span>Upstream</span>
                    <small>
                      {journey.data.upstream
                        .map((item) => item.label)
                        .join(', ') || 'none'}
                    </small>
                  </div>
                  <div className="phlo-v2-mini-row">
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
                <div className="phlo-v2-panel-footer">{journey.error}</div>
              )}
              {stageDiff.data && (
                <div className="phlo-v2-detail-list">
                  <div className="phlo-v2-mini-row">
                    <span>
                      <GitCompare className="size-3.5" />
                      Stage diff
                    </span>
                    <small>
                      {stageDiff.data.source.name} {'->'}{' '}
                      {stageDiff.data.target.name}
                    </small>
                  </div>
                  <div className="phlo-v2-mini-row">
                    <span>Changed rows</span>
                    <small>{stageDiff.data.summary.changed ?? 0}</small>
                  </div>
                  <div className="phlo-v2-mini-row">
                    <span>Added columns</span>
                    <small>
                      {(stageDiff.data.columns.added ?? []).join(', ') ||
                        'none'}
                    </small>
                  </div>
                </div>
              )}
              {stageDiff.error && (
                <div className="phlo-v2-panel-footer">{stageDiff.error}</div>
              )}
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
                label="Preview rows"
                value={`${preview.rows.length} loaded${preview.has_more ? ' · more available' : ''}`}
              />
              <Mini label="Namespace" value={table.namespace ?? 'default'} />
              {table.asset_id && (
                <Link
                  className="phlo-v2-mini-row"
                  to="/v2/asset/$assetId"
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
        <div className="phlo-v2-empty-state">
          {result.error ?? 'Loading table detail...'}
        </div>
      )}
    </V2Page>
  )
}

function inferSourceTableId(tableId: string): string | null {
  if (tableId.includes('orders_clean')) return 'orders'
  if (tableId.includes('revenue_daily')) return 'orders_clean'
  if (tableId.includes('customer_health')) return 'revenue_daily'
  if (tableId.includes('customers')) return 'orders'
  return null
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

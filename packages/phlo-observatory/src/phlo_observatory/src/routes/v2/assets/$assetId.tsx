import { createFileRoute } from '@tanstack/react-router'
import {
  Clock3,
  Columns3,
  Database,
  GitBranch,
  ShieldCheck,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import type { V2AssetDetail, V2ResourceResult } from '@/v2/api/types'
import { getV2AssetDetail } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { readMetric } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/assets/$assetId')({
  component: AssetDetailRoute,
})

function AssetDetailRoute() {
  const { assetId } = Route.useParams()
  return <AssetDetailView assetId={assetId} />
}

export function AssetDetailView({ assetId }: { assetId: string }) {
  const [result, setResult] = useState<V2ResourceResult<V2AssetDetail>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getV2AssetDetail({ data: { assetId } }).then(setResult)
  }, [assetId])

  const detail = result.data
  const asset = detail?.asset

  return (
    <V2Page
      action={<span className="phlo-v2-pill">{asset?.group ?? 'asset'}</span>}
      description="Asset impact, quality, lineage, and activity."
      kicker="Asset"
      title={asset?.name ?? assetId}
    >
      {asset ? (
        <section className="phlo-v2-surface-grid">
          <div className="phlo-v2-list-surface">
            <div className="phlo-v2-browser-toolbar">
              <span>
                <Database className="size-4" />
                Facts
              </span>
            </div>
            <dl className="phlo-v2-facts phlo-v2-facts-panel">
              <dt>Freshness</dt>
              <dd>{readMetric(asset.metadata, 'freshness') ?? 'n/a'}</dd>
              <dt>Records</dt>
              <dd>{readMetric(asset.metadata, 'records') ?? 'n/a'}</dd>
              <dt>Format</dt>
              <dd>{readMetric(asset.metadata, 'format') ?? 'n/a'}</dd>
              <dt>Branch</dt>
              <dd>{readMetric(asset.metadata, 'branch') ?? 'main'}</dd>
            </dl>
          </div>
          <aside className="phlo-v2-inspector">
            <div className="phlo-v2-inspector-label">Impact</div>
            <h2>{asset.name}</h2>
            <p>{asset.description ?? 'No description returned.'}</p>
            <div className="phlo-v2-detail-list">
              <Mini
                label="Upstream"
                value={
                  detail.upstream.map((item) => item.name).join(', ') || 'none'
                }
              />
              <Mini
                label="Downstream"
                value={
                  detail.downstream.map((item) => item.name).join(', ') ||
                  'none'
                }
              />
              <Mini label="Tables" value={String(detail.tables.length)} />
              <Mini label="Quality" value={String(detail.quality.length)} />
              <Mini
                label="Materializations"
                value={String(detail.materializations.length)}
              />
            </div>
            <div className="phlo-v2-detail-list">
              {Object.entries(detail.column_lineage)
                .slice(0, 5)
                .map(([column, sources]) => (
                  <div className="phlo-v2-mini-row" key={column}>
                    <span>
                      <Columns3 className="size-3" />
                      {column}
                    </span>
                    <small>{sources.join(', ') || 'source column'}</small>
                  </div>
                ))}
              {detail.materializations.slice(0, 3).map((operation) => (
                <div className="phlo-v2-mini-row" key={operation.id}>
                  <span>
                    <Clock3 className="size-3" />
                    {operation.name}
                  </span>
                  <small>
                    {[operation.status, operation.completed_at]
                      .filter(Boolean)
                      .join(' · ')}
                  </small>
                </div>
              ))}
            </div>
            <div className="phlo-v2-chip-cloud">
              {asset.dependencies.map((dependency) => (
                <span className="phlo-v2-chip" key={dependency}>
                  <GitBranch className="size-3" />
                  {dependency}
                </span>
              ))}
              {asset.checks.map((check) => (
                <span className="phlo-v2-chip" key={check}>
                  <ShieldCheck className="size-3" />
                  {check}
                </span>
              ))}
            </div>
          </aside>
        </section>
      ) : (
        <div className="phlo-v2-empty-state">
          {result.error ?? 'Loading asset detail...'}
        </div>
      )}
    </V2Page>
  )
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="phlo-v2-mini-row">
      <span>{label}</span>
      <small>{value}</small>
    </div>
  )
}

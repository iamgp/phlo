import { createFileRoute } from '@tanstack/react-router'
import {
  Clock3,
  Columns3,
  Database,
  GitBranch,
  ShieldCheck,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import type {
  ObservatoryAssetDetail,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import { getObservatoryAssetDetail } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { readMetric } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/assets/$assetId')({
  component: AssetDetailRoute,
})

function AssetDetailRoute() {
  const { assetId } = Route.useParams()
  return <AssetDetailView assetId={assetId} />
}

export function AssetDetailView({ assetId }: { assetId: string }) {
  const [result, setResult] = useState<
    ObservatoryResourceResult<ObservatoryAssetDetail>
  >({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getObservatoryAssetDetail({ data: { assetId } })
      .then(setResult)
      .catch(() =>
        setResult({
          data: null,
          error: 'Asset detail is unavailable.',
        }),
      )
  }, [assetId])

  const detail = result.data
  const asset = detail?.asset

  return (
    <ObservatoryPage
      action={
        <span className="phlo-observatory-pill">{asset?.group ?? 'asset'}</span>
      }
      description="Asset impact, quality, lineage, and activity."
      kicker="Asset"
      title={asset?.name ?? assetId}
    >
      {asset ? (
        <section className="phlo-observatory-surface-grid">
          <div className="phlo-observatory-list-surface">
            <div className="phlo-observatory-browser-toolbar">
              <span>
                <Database className="size-4" />
                Facts
              </span>
            </div>
            <dl className="phlo-observatory-facts phlo-observatory-facts-panel">
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
          <aside className="phlo-observatory-inspector">
            <div className="phlo-observatory-inspector-label">Impact</div>
            <h2>{asset.name}</h2>
            <p>{asset.description ?? 'No description returned.'}</p>
            <div className="phlo-observatory-detail-list">
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
            <div className="phlo-observatory-detail-list">
              {Object.entries(detail.column_lineage)
                .slice(0, 5)
                .map(([column, sources]) => (
                  <div className="phlo-observatory-mini-row" key={column}>
                    <span>
                      <Columns3 className="size-3" />
                      {column}
                    </span>
                    <small>{sources.join(', ') || 'source column'}</small>
                  </div>
                ))}
              {detail.materializations.slice(0, 3).map((operation) => (
                <div className="phlo-observatory-mini-row" key={operation.id}>
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
            <div className="phlo-observatory-chip-cloud">
              {asset.dependencies.map((dependency) => (
                <span className="phlo-observatory-chip" key={dependency}>
                  <GitBranch className="size-3" />
                  {dependency}
                </span>
              ))}
              {asset.checks.map((check) => (
                <span className="phlo-observatory-chip" key={check}>
                  <ShieldCheck className="size-3" />
                  {check}
                </span>
              ))}
            </div>
          </aside>
        </section>
      ) : (
        <div className="phlo-observatory-empty-state">
          {result.error ?? 'Loading asset detail…'}
        </div>
      )}
    </ObservatoryPage>
  )
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="phlo-observatory-mini-row">
      <span>{label}</span>
      <small>{value}</small>
    </div>
  )
}

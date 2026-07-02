import { Link, createFileRoute } from '@tanstack/react-router'
import { Activity, PlayCircle } from 'lucide-react'

import type { ObservatoryDataProductPipeline } from '@/observatory/api/types'
import { getObservatoryPipelineRecords } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { StatusBadge } from '@/observatory/components/StatusBadge'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/pipelines')({
  component: Pipelines,
})

export function Pipelines() {
  const result = useLiveResource(
    getObservatoryPipelineRecords,
    120_000,
    'v2:pipelines',
  )
  const pipelines = result.data ?? []

  return (
    <ObservatoryPage
      kicker="Pipelines"
      title="Production Flow"
      description="Read-only Data Product flow across ingestion, transforms, checks, publishing, freshness, and runs."
      action={
        <span className="phlo-observatory-pill">{pipelines.length} flows</span>
      }
    >
      <section className="phlo-observatory-command phlo-observatory-surface-shell">
        <div className="phlo-observatory-command-primary phlo-observatory-surface-list">
          <div className="phlo-observatory-browser-toolbar">
            <div className="phlo-observatory-row-title">
              <Activity className="size-4" />
              Data Product flows
            </div>
          </div>
          {result.error ? (
            <EmptyFlow detail={result.error} />
          ) : pipelines.length ? (
            <div className="phlo-observatory-list">
              {pipelines.map((pipeline) => (
                <PipelineRow
                  key={pipeline.product?.id ?? pipeline.freshness_at}
                  pipeline={pipeline}
                />
              ))}
            </div>
          ) : (
            <EmptyFlow detail="No Data Product pipelines returned." />
          )}
        </div>
        <aside className="phlo-observatory-inspector phlo-observatory-surface-inspector">
          <div className="phlo-observatory-inspector-label">Actions</div>
          <h2>Guarded operations</h2>
          <p>
            Retry, cancel, materialize, and backfill appear only as supported
            action descriptors. Pipeline definition editing is not available
            here.
          </p>
        </aside>
      </section>
    </ObservatoryPage>
  )
}

function PipelineRow({
  pipeline,
}: {
  pipeline: ObservatoryDataProductPipeline
}) {
  const product = pipeline.product
  return (
    <div className="phlo-observatory-pipeline-row">
      <span
        className="phlo-observatory-dot"
        data-state={pipeline.freshness_state}
      />
      <div className="phlo-observatory-pipeline-main">
        <div className="phlo-observatory-row-title">
          <PlayCircle className="size-4" />
          {product ? (
            <Link
              params={{ productId: product.id }}
              to="/data-products/$productId"
            >
              {product.name}
            </Link>
          ) : (
            'Pipeline'
          )}
        </div>
        <div className="phlo-observatory-row-meta">
          {pipeline.last_run?.label ?? 'No run returned'} · freshness{' '}
          {pipeline.freshness_at ?? pipeline.freshness_state}
        </div>
        <div className="phlo-observatory-pipeline-grid">
          {pipeline.stages.map((stage) => (
            <div className="phlo-observatory-pipeline-cell" key={stage.id}>
              <span>{stage.label}</span>
              <small>{stage.state}</small>
            </div>
          ))}
          {pipeline.actions.map((action) => (
            <div className="phlo-observatory-pipeline-cell" key={action.id}>
              <span>{action.label}</span>
              <small>{action.enabled ? 'available' : action.reason}</small>
            </div>
          ))}
        </div>
      </div>
      <StatusBadge
        label={pipeline.freshness_state}
        state={pipeline.freshness_state}
      />
    </div>
  )
}

function EmptyFlow({ detail }: { detail: string }) {
  return (
    <div className="phlo-observatory-operation-empty">
      <div>
        <span className="phlo-observatory-inspector-label">Pipelines</span>
        <h2>No production flow</h2>
        <p>{detail}</p>
      </div>
    </div>
  )
}

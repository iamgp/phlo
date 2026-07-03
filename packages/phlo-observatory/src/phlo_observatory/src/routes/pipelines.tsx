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
      title="Product pipelines"
      description="Product flow, freshness, and guarded actions. Use Runs for history and Operations for recovery."
      action={
        <span className="phlo-observatory-pill">{pipelines.length} flows</span>
      }
    >
      <section className="phlo-observatory-command phlo-observatory-surface-shell">
        <div className="phlo-observatory-command-primary phlo-observatory-surface-list">
          <div className="phlo-observatory-browser-toolbar">
            <div className="phlo-observatory-row-title">
              <Activity className="size-4" />
              Product flows
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
            Retry, cancel, materialize, and backfill appear when the current run
            supports them. Run history and recovery logs live in Operations.
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
      <div className="phlo-observatory-pipeline-product">
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
          {pipeline.last_run?.label ?? 'No run returned'}
        </div>
      </div>
      <div className="phlo-observatory-pipeline-run">
        <span>Freshness</span>
        <small>{pipeline.freshness_at ?? pipeline.freshness_state}</small>
      </div>
      <div className="phlo-observatory-pipeline-stages">
        {pipeline.stages.map((stage) => (
          <span
            className="phlo-observatory-pipeline-stage"
            data-state={stage.state}
            key={stage.id}
          >
            <strong>{stage.label}</strong>
            <small>{stage.state}</small>
          </span>
        ))}
      </div>
      <div className="phlo-observatory-pipeline-actions">
        {pipeline.actions.map((action) => (
          <span
            className="phlo-observatory-pipeline-action"
            data-enabled={action.enabled}
            key={action.id}
            title={action.enabled ? undefined : action.reason}
          >
            {action.label}
          </span>
        ))}
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

import { Layers3 } from 'lucide-react'

import type { V2ResourceResult, V2SurfaceItem } from '@/v2/api/types'
import { V2Page } from '@/v2/components/V2Page'

export function V2SurfacePage({
  contract,
  description,
  emptyCopy,
  error,
  items,
  kicker,
  title,
}: {
  contract: string
  description: string
  emptyCopy: string
  error: V2ResourceResult<Array<V2SurfaceItem>>['error']
  items: Array<V2SurfaceItem>
  kicker: string
  title: string
}) {
  return (
    <V2Page
      kicker={kicker}
      title={title}
      description={description}
      action={<span className="phlo-v2-pill">{items.length} items</span>}
    >
      <section className="phlo-v2-command phlo-v2-surface-shell">
        <div className="phlo-v2-command-primary phlo-v2-surface-list">
          <div className="phlo-v2-list">
            {items.map((item) => (
              <SurfaceRow item={item} key={item.id} />
            ))}
            {items.length === 0 && error && (
              <div className="phlo-v2-operation-empty">
                <div>
                  <span className="phlo-v2-inspector-label">
                    Surface unavailable
                  </span>
                  <h2>{title} could not load.</h2>
                  <p>{error}</p>
                </div>
                <div className="phlo-v2-detail-list">
                  <div className="phlo-v2-mini-row">
                    <span>Contract</span>
                    <small>{contract}</small>
                  </div>
                  <div className="phlo-v2-mini-row">
                    <span>Status</span>
                    <small>error</small>
                  </div>
                </div>
              </div>
            )}
            {items.length === 0 && !error && (
              <div className="phlo-v2-operation-empty">
                <div>
                  <span className="phlo-v2-inspector-label">
                    No items returned
                  </span>
                  <h2>{title} has no items yet.</h2>
                  <p>{emptyCopy}</p>
                </div>
                <div className="phlo-v2-detail-list">
                  <div className="phlo-v2-mini-row">
                    <span>Contract</span>
                    <small>{contract}</small>
                  </div>
                  <div className="phlo-v2-mini-row">
                    <span>Rows</span>
                    <small>0 returned</small>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <aside className="phlo-v2-inspector phlo-v2-surface-inspector">
          <div className="phlo-v2-inspector-label">Surface contract</div>
          <h2>{kicker}</h2>
          <p>{description}</p>
          <dl className="phlo-v2-facts">
            <dt>Endpoint</dt>
            <dd>{contract}</dd>
            <dt>Items</dt>
            <dd>{items.length}</dd>
          </dl>
          {error && items.length > 0 && (
            <div className="phlo-v2-panel-footer">{error}</div>
          )}
        </aside>
      </section>
    </V2Page>
  )
}

function SurfaceRow({ item }: { item: V2SurfaceItem }) {
  return (
    <div className="phlo-v2-timeline-row">
      <span className="phlo-v2-dot" data-state={item.health.state} />
      <div>
        <div className="phlo-v2-row-title">
          <Layers3 className="size-4" />
          {item.name}
        </div>
        <div className="phlo-v2-row-meta">
          {[item.kind, item.summary].filter(Boolean).join(' · ')}
        </div>
      </div>
      <span className="phlo-v2-pill">{item.health.state}</span>
    </div>
  )
}

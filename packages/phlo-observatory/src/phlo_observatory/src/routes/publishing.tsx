import { Link, createFileRoute } from '@tanstack/react-router'
import { UploadCloud } from 'lucide-react'

import type { ObservatoryDataProduct } from '@/observatory/api/types'
import { getObservatoryDataProductRecords } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { StatusBadge } from '@/observatory/components/StatusBadge'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/publishing')({
  component: Publishing,
})

export function Publishing() {
  const result = useLiveResource(
    getObservatoryDataProductRecords,
    120_000,
    'v2:data-products',
  )
  const products = result.data ?? []
  const promoted = products.filter((product) => !product.candidate)
  const published = promoted.filter(
    (product) => product.publication_state === 'published',
  )
  const drafts = promoted.filter(
    (product) => product.publication_state === 'draft',
  )

  return (
    <ObservatoryPage
      kicker="Publishing"
      title="Publishing Readiness"
      description="Review Data Product publication state and open profiles for guarded publish or retire actions."
      action={
        <span className="phlo-observatory-pill">
          {published.length} published
        </span>
      }
    >
      <section className="phlo-observatory-command phlo-observatory-surface-shell">
        <div className="phlo-observatory-command-primary phlo-observatory-surface-list">
          <div className="phlo-observatory-browser-toolbar">
            <div className="phlo-observatory-row-title">
              <UploadCloud className="size-4" />
              Publication states
            </div>
          </div>
          {result.error ? (
            <EmptyPublishing detail={result.error} />
          ) : promoted.length ? (
            <div className="phlo-observatory-list">
              {promoted.map((product) => (
                <PublishingRow key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <EmptyPublishing detail="No promoted Data Products returned." />
          )}
        </div>

        <aside className="phlo-observatory-inspector phlo-observatory-surface-inspector">
          <div className="phlo-observatory-inspector-label">Policy</div>
          <h2>Internal publication</h2>
          <p>
            Publishing is capability-aware and internal-only here. External
            sharing, marketplace listing, and public access are not created by
            these controls.
          </p>
          <dl className="phlo-observatory-facts">
            <dt>Promoted</dt>
            <dd>{promoted.length}</dd>
            <dt>Draft</dt>
            <dd>{drafts.length}</dd>
            <dt>Published</dt>
            <dd>{published.length}</dd>
          </dl>
        </aside>
      </section>
    </ObservatoryPage>
  )
}

function PublishingRow({ product }: { product: ObservatoryDataProduct }) {
  return (
    <Link
      className="phlo-observatory-product-row"
      params={{ productId: product.id }}
      to="/data-products/$productId"
    >
      <span
        className="phlo-observatory-dot"
        data-state={product.readiness_state}
      />
      <div>
        <div className="phlo-observatory-row-title">
          <UploadCloud className="size-4" />
          {product.name}
        </div>
        <div className="phlo-observatory-row-meta">
          {[
            product.owner ? `Owner ${product.owner}` : 'No owner',
            product.classifications.join(', ') || 'unclassified',
            product.source_refs.map((ref) => ref.kind).join(', ') || 'source',
          ].join(' · ')}
        </div>
      </div>
      <StatusBadge
        label={product.publication_state}
        state={product.readiness_state}
      />
    </Link>
  )
}

function EmptyPublishing({ detail }: { detail: string }) {
  return (
    <div className="phlo-observatory-operation-empty">
      <div>
        <span className="phlo-observatory-inspector-label">Publishing</span>
        <h2>No publication state</h2>
        <p>{detail}</p>
      </div>
    </div>
  )
}

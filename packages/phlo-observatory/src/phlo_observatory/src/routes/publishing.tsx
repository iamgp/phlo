import { Link, createFileRoute } from '@tanstack/react-router'
import { Archive, ShieldAlert, UploadCloud } from 'lucide-react'
import { useState } from 'react'

import type { ObservatoryDataProduct } from '@/observatory/api/types'
import {
  getObservatoryDataProductRecords,
  runObservatoryActionDirect,
} from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { StatusBadge } from '@/observatory/components/StatusBadge'
import { invalidateCachedResources } from '@/observatory/routes/liveResource'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/publishing')({
  component: Publishing,
})

export function Publishing() {
  const [actionMessage, setActionMessage] = useState<string | null>(null)
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
      title="Publication readiness"
      description="Review internal publication state, blockers, and guarded publish or retire actions."
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
                <PublishingRow
                  key={product.id}
                  onAction={(actionId) => {
                    setActionMessage('Requesting publication action...')
                    void runObservatoryActionDirect({ actionId }).then(
                      (next) => {
                        invalidateCachedResources([
                          'v2:data-products',
                          'v2:operations',
                        ])
                        window.dispatchEvent(new Event('focus'))
                        setActionMessage(
                          next.data?.message ??
                            next.error ??
                            'Action requested',
                        )
                      },
                    )
                  }}
                  product={product}
                />
              ))}
            </div>
          ) : (
            <EmptyPublishing detail="No promoted Data Products returned." />
          )}
          {actionMessage && (
            <div className="phlo-observatory-panel-footer">{actionMessage}</div>
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

function PublishingRow({
  onAction,
  product,
}: {
  onAction: (actionId: string) => void
  product: ObservatoryDataProduct
}) {
  const blockers = publicationBlockers(product)
  const approval = approvalState(product, blockers)
  const nextAction = publicationNextAction(product, blockers)
  const canPublish =
    product.publication_state !== 'published' &&
    blockers.length === 0 &&
    product.readiness_state === 'ok'
  const canRetire = product.publication_state === 'published'
  const publishReason =
    blockers.join(', ') ||
    (product.readiness_state === 'warning'
      ? 'readiness warning needs review'
      : 'readiness evidence missing')

  return (
    <div className="phlo-observatory-product-row phlo-observatory-publication-row">
      <span
        className="phlo-observatory-dot"
        data-state={product.readiness_state}
      />
      <div>
        <Link
          className="phlo-observatory-row-title"
          params={{ productId: product.id }}
          to="/data-products/$productId"
        >
          <UploadCloud className="size-4" />
          {product.name}
        </Link>
        <div className="phlo-observatory-row-meta">
          {[
            product.owner ? `Owner ${product.owner}` : 'No owner',
            `Approval ${approval}`,
            blockers.join(', ') || 'ready',
          ].join(' · ')}
        </div>
      </div>
      <div className="phlo-observatory-publication-actions">
        <StatusBadge
          label={product.publication_state}
          state={product.readiness_state}
        />
        <span>{nextAction}</span>
        <div className="phlo-observatory-inline-actions">
          <button
            disabled={!canPublish}
            onClick={() => onAction(`data-product:${product.id}:publish`)}
            title={canPublish ? 'Publish internally' : publishReason}
            type="button"
          >
            <UploadCloud className="size-3.5" />
            Publish
          </button>
          <button
            disabled={!canRetire}
            onClick={() => onAction(`data-product:${product.id}:retire`)}
            title={
              canRetire
                ? 'Retire internally'
                : 'Only published products can be retired'
            }
            type="button"
          >
            <Archive className="size-3.5" />
            Retire
          </button>
        </div>
      </div>
    </div>
  )
}

function publicationBlockers(product: ObservatoryDataProduct): Array<string> {
  const blockers: Array<string> = []
  if (!product.owner) blockers.push('owner missing')
  if (product.classifications.length === 0)
    blockers.push('classification missing')
  if (product.readiness_state === 'error') blockers.push('quality blocking')
  if (product.readiness_state === 'unknown') blockers.push('evidence missing')
  return blockers
}

function approvalState(
  product: ObservatoryDataProduct,
  blockers: Array<string>,
): string {
  const explicit = product.metadata.approval_state
  if (typeof explicit === 'string' && explicit.trim()) return explicit
  if (product.publication_state === 'published') return 'approved'
  if (blockers.length > 0) return 'blocked'
  if (product.readiness_state === 'warning') return 'review'
  return 'ready'
}

function publicationNextAction(
  product: ObservatoryDataProduct,
  blockers: Array<string>,
): string {
  if (product.publication_state === 'published') return 'Retire if obsolete'
  if (blockers.length > 0) return 'Resolve blockers'
  if (product.readiness_state === 'warning') return 'Review warning'
  return 'Publish internally'
}

function EmptyPublishing({ detail }: { detail: string }) {
  return (
    <div className="phlo-observatory-operation-empty">
      <div>
        <span className="phlo-observatory-inspector-label">Publishing</span>
        <h2>No publication state</h2>
        <p>
          <ShieldAlert className="size-4" />
          {detail}
        </p>
      </div>
    </div>
  )
}

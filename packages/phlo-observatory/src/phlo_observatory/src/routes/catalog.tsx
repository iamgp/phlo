import { Link, createFileRoute } from '@tanstack/react-router'
import { Boxes, Filter, Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import type { ObservatoryDataProduct } from '@/observatory/api/types'
import { getObservatoryDataProductRecords } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { StatusBadge } from '@/observatory/components/StatusBadge'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/catalog')({
  component: Catalog,
})

export function Catalog() {
  const result = useLiveResource(
    getObservatoryDataProductRecords,
    120_000,
    'v2:data-products',
  )
  const products = result.data ?? []
  const [query, setQuery] = useState('')
  const [owner, setOwner] = useState('all')
  const [classification, setClassification] = useState('all')
  const [publicationState, setPublicationState] = useState('all')
  const [readinessState, setReadinessState] = useState('all')

  const promoted = products.filter((product) => !product.candidate)
  const candidates = products.filter((product) => product.candidate)
  const owners = optionValues(promoted.map((product) => product.owner))
  const classifications = optionValues(
    promoted.flatMap((product) => product.classifications),
  )
  const filtered = useMemo(
    () =>
      promoted.filter((product) =>
        matchesProduct(product, {
          classification,
          owner,
          publicationState,
          query,
          readinessState,
        }),
      ),
    [classification, owner, promoted, publicationState, query, readinessState],
  )

  return (
    <ObservatoryPage
      kicker="Catalog"
      title="Data Products"
      description="Browse promoted Data Products first, then inspect raw candidates that look ready to be claimed."
      action={
        <span className="phlo-observatory-pill">{products.length} items</span>
      }
    >
      <section className="phlo-observatory-command phlo-observatory-surface-shell">
        <div className="phlo-observatory-command-primary phlo-observatory-surface-list">
          <div className="phlo-observatory-browser-toolbar">
            <label className="phlo-observatory-search-field">
              <Search className="size-4" />
              <input
                aria-label="Search Data Products"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search Data Products"
                value={query}
              />
            </label>
          </div>
          <div className="phlo-observatory-catalog-filters">
            <SelectFilter
              label="Owner"
              onChange={setOwner}
              value={owner}
              values={owners}
            />
            <SelectFilter
              label="Classification"
              onChange={setClassification}
              value={classification}
              values={classifications}
            />
            <SelectFilter
              label="Publication"
              onChange={setPublicationState}
              value={publicationState}
              values={['draft', 'published', 'retired']}
            />
            <SelectFilter
              label="Readiness"
              onChange={setReadinessState}
              value={readinessState}
              values={['ok', 'warning', 'error', 'unknown']}
            />
          </div>
          <ProductList error={result.error} products={filtered} />
        </div>

        <aside className="phlo-observatory-inspector phlo-observatory-surface-inspector">
          <div className="phlo-observatory-inspector-label">Catalog</div>
          <h2>{filtered.length} Data Products</h2>
          <p>
            Search stays intentionally small until profiles are rich enough for
            deeper ranking.
          </p>
          <dl className="phlo-observatory-facts">
            <dt>Promoted</dt>
            <dd>{promoted.length}</dd>
            <dt>Candidates</dt>
            <dd>{candidates.length}</dd>
            <dt>Published</dt>
            <dd>
              {
                promoted.filter(
                  (product) => product.publication_state === 'published',
                ).length
              }
            </dd>
          </dl>
          <div className="phlo-observatory-detail-list">
            <div className="phlo-observatory-mini-row">
              <span>Candidate Data Products</span>
              <small>manual promotion required</small>
            </div>
            {candidates.slice(0, 6).map((candidate) => (
              <div className="phlo-observatory-mini-row" key={candidate.id}>
                <span>{candidate.name}</span>
                <small>
                  {candidate.source_refs.map((ref) => ref.kind).join(', ')}
                </small>
              </div>
            ))}
            {candidates.length === 0 && (
              <div className="phlo-observatory-mini-row">
                <span>No candidates returned</span>
                <small>empty</small>
              </div>
            )}
          </div>
        </aside>
      </section>
    </ObservatoryPage>
  )
}

function ProductList({
  error,
  products,
}: {
  error: string | null
  products: Array<ObservatoryDataProduct>
}) {
  if (products.length === 0) {
    return (
      <div className="phlo-observatory-operation-empty">
        <div>
          <span className="phlo-observatory-inspector-label">
            {error ? 'Catalog unavailable' : 'No Data Products returned'}
          </span>
          <h2>
            {error
              ? 'Catalog could not load.'
              : 'No promoted Data Products found.'}
          </h2>
          <p>
            {error ??
              'Promote raw assets into Data Products to make them appear here.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="phlo-observatory-list">
      {products.map((product) => (
        <Link
          className="phlo-observatory-timeline-row"
          key={product.id}
          params={{ productId: product.id }}
          to="/data-products/$productId"
        >
          <span
            className="phlo-observatory-dot"
            data-state={product.readiness_state}
          />
          <div>
            <div className="phlo-observatory-row-title">
              <Boxes className="size-4" />
              {product.name}
            </div>
            <div className="phlo-observatory-row-meta">
              {[
                product.owner ? `Owner ${product.owner}` : 'No owner',
                product.classifications.join(', ') || 'unclassified',
                product.source_refs.map((ref) => ref.kind).join(', ') ||
                  'source',
              ].join(' · ')}
            </div>
          </div>
          <StatusBadge
            label={product.publication_state}
            state={product.readiness_state}
          />
        </Link>
      ))}
    </div>
  )
}

function SelectFilter({
  label,
  onChange,
  value,
  values,
}: {
  label: string
  onChange: (value: string) => void
  value: string
  values: Array<string>
}) {
  return (
    <label className="phlo-observatory-filter-field">
      <Filter className="size-3.5" />
      <span>{label}</span>
      <select onChange={(event) => onChange(event.target.value)} value={value}>
        <option value="all">All</option>
        {values.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </label>
  )
}

function matchesProduct(
  product: ObservatoryDataProduct,
  filters: {
    classification: string
    owner: string
    publicationState: string
    query: string
    readinessState: string
  },
) {
  const query = filters.query.trim().toLowerCase()
  const haystack = [
    product.name,
    product.description ?? '',
    product.owner ?? '',
    product.classifications.join(' '),
    product.source_refs.map((ref) => ref.label).join(' '),
  ]
    .join(' ')
    .toLowerCase()
  return (
    (!query || haystack.includes(query)) &&
    (filters.owner === 'all' || product.owner === filters.owner) &&
    (filters.classification === 'all' ||
      product.classifications.includes(filters.classification)) &&
    (filters.publicationState === 'all' ||
      product.publication_state === filters.publicationState) &&
    (filters.readinessState === 'all' ||
      product.readiness_state === filters.readinessState)
  )
}

function optionValues(values: Array<string | null | undefined>) {
  return Array.from(
    new Set(values.filter((value): value is string => Boolean(value))),
  ).sort()
}

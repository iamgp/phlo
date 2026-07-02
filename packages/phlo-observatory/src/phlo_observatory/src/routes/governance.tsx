import { Link, createFileRoute } from '@tanstack/react-router'
import { FileCheck2, ShieldCheck } from 'lucide-react'
import { useMemo, useState } from 'react'

import { getObservatoryGovernanceItems } from '@/observatory/api/resources'
import type {
  ObservatoryControlStatus,
  ObservatoryGovernanceRow,
} from '@/observatory/api/types'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/governance')({
  component: Governance,
})

export function Governance() {
  const result = useLiveResource(
    getObservatoryGovernanceItems,
    120_000,
    'v2:governance-matrix',
  )
  const matrix = result.data
  const rows = matrix?.rows ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected = useMemo(
    () => rows.find((row) => row.product.id === selectedId) ?? rows[0] ?? null,
    [rows, selectedId],
  )

  return (
    <ObservatoryPage
      kicker="Governance"
      title="Data Product Controls"
      description="Scan ownership, classification, and evidence-backed controls across Data Products."
      action={
        <span className="phlo-observatory-pill">{rows.length} products</span>
      }
    >
      <section className="phlo-observatory-command phlo-observatory-surface-shell">
        <div className="phlo-observatory-command-primary phlo-observatory-surface-list">
          <div className="phlo-observatory-browser-toolbar">
            <div className="phlo-observatory-row-title">
              <ShieldCheck className="size-4" />
              Control matrix
            </div>
          </div>
          {result.error ? (
            <EmptyMatrix
              title="Governance could not load"
              detail={result.error}
            />
          ) : rows.length ? (
            <ControlMatrix
              onSelect={setSelectedId}
              rows={rows}
              selectedId={selected?.product.id ?? null}
            />
          ) : (
            <EmptyMatrix
              title="No Data Product controls returned"
              detail="Create Data Products to populate the governance matrix."
            />
          )}
        </div>
        <GovernanceInspector row={selected} />
      </section>
    </ObservatoryPage>
  )
}

function ControlMatrix({
  onSelect,
  rows,
  selectedId,
}: {
  onSelect: (id: string) => void
  rows: Array<ObservatoryGovernanceRow>
  selectedId: string | null
}) {
  return (
    <div className="phlo-observatory-governance-matrix">
      <div className="phlo-observatory-governance-row phlo-observatory-governance-header">
        <span>Data Product</span>
        <span>Owner</span>
        <span>Classification</span>
        <span>Blocking quality</span>
      </div>
      {rows.map((row) => (
        <button
          className="phlo-observatory-governance-row"
          data-selected={selectedId === row.product.id}
          key={row.product.id}
          onClick={() => onSelect(row.product.id)}
          type="button"
        >
          <span>
            <strong>{row.product.name}</strong>
            <small>{row.product.publication_state}</small>
          </span>
          {row.controls.map((control) => (
            <span
              className="phlo-observatory-control-cell"
              data-label={controlHeader(control.id)}
              key={control.id}
            >
              <span
                className="phlo-observatory-dot"
                data-state={controlHealth(control.status)}
              />
              {controlLabel(control.status)}
            </span>
          ))}
        </button>
      ))}
    </div>
  )
}

function GovernanceInspector({
  row,
}: {
  row: ObservatoryGovernanceRow | null
}) {
  if (!row) {
    return (
      <aside className="phlo-observatory-inspector phlo-observatory-surface-inspector">
        <div className="phlo-observatory-inspector-label">Evidence</div>
        <h2>No product selected</h2>
        <p>Governance evidence appears once Data Products are returned.</p>
      </aside>
    )
  }

  const evidenceCount = row.controls.reduce(
    (count, control) => count + control.evidence.length,
    0,
  )
  return (
    <aside className="phlo-observatory-inspector phlo-observatory-surface-inspector">
      <div className="phlo-observatory-inspector-label">Evidence</div>
      <h2>{row.product.name}</h2>
      <p>
        {row.product.description ?? 'Control evidence for this Data Product.'}
      </p>
      <dl className="phlo-observatory-facts">
        <dt>Owner</dt>
        <dd>{row.owner ?? 'unassigned'}</dd>
        <dt>Classification</dt>
        <dd>{row.classifications.join(', ') || 'none'}</dd>
        <dt>Evidence</dt>
        <dd>{evidenceCount}</dd>
      </dl>
      <div className="phlo-observatory-detail-list">
        {row.controls.map((control) => (
          <div className="phlo-observatory-mini-row" key={control.id}>
            <span>{control.label}</span>
            <small>{controlLabel(control.status)}</small>
            <p>{control.message}</p>
            {control.evidence.map((evidence) => (
              <EvidenceRow evidence={evidence} key={evidence.id} />
            ))}
          </div>
        ))}
      </div>
    </aside>
  )
}

function EmptyMatrix({ detail, title }: { detail: string; title: string }) {
  return (
    <div className="phlo-observatory-operation-empty">
      <div>
        <span className="phlo-observatory-inspector-label">Matrix</span>
        <h2>{title}</h2>
        <p>{detail}</p>
      </div>
    </div>
  )
}

function controlHealth(status: ObservatoryControlStatus) {
  if (status === 'pass') return 'ok'
  if (status === 'fail') return 'error'
  if (status === 'warning') return 'warning'
  return 'unknown'
}

function controlLabel(status: ObservatoryControlStatus) {
  return status.replace('_', ' ')
}

function controlHeader(controlId: string) {
  if (controlId === 'owner') return 'Owner'
  if (controlId === 'classification') return 'Classification'
  if (controlId === 'blocking_quality') return 'Blocking quality'
  return controlId
}

function EvidenceRow({
  evidence,
}: {
  evidence: ObservatoryGovernanceRow['controls'][number]['evidence'][number]
}) {
  const content = (
    <>
      <span>
        <FileCheck2 className="size-3.5" />
        {evidence.label}
      </span>
      <small>{evidence.value ?? evidence.kind}</small>
    </>
  )
  if (evidence.resource?.kind === 'data_product') {
    return (
      <Link
        className="phlo-observatory-mini-row"
        params={{ productId: evidence.resource.id }}
        to="/data-products/$productId"
      >
        {content}
      </Link>
    )
  }
  return <div className="phlo-observatory-mini-row">{content}</div>
}

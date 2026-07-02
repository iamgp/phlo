import { Link, createFileRoute } from '@tanstack/react-router'
import {
  Boxes,
  Database,
  GitBranch,
  ListChecks,
  ShieldCheck,
  UserRound,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import { getObservatoryDataProductProfileDirect } from '@/observatory/api/resources'
import type {
  ObservatoryDataProductProfile,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { StatusBadge } from '@/observatory/components/StatusBadge'

export const Route = createFileRoute('/data-products/$productId')({
  component: DataProductProfileRoute,
})

function DataProductProfileRoute() {
  const { productId } = Route.useParams()
  return <DataProductProfile productId={productId} />
}

export function DataProductProfile({ productId }: { productId: string }) {
  const [result, setResult] = useState<
    ObservatoryResourceResult<ObservatoryDataProductProfile>
  >({ data: null, error: null })

  useEffect(() => {
    let cancelled = false
    void getObservatoryDataProductProfileDirect({ productId }).then((next) => {
      if (!cancelled) setResult(next)
    })
    return () => {
      cancelled = true
    }
  }, [productId])

  const profile = result.data
  const product = profile?.product

  return (
    <ObservatoryPage
      kicker="Data Product"
      title={product?.name ?? productId}
      description={
        product?.description ??
        'Shared product profile for ownership, lineage, quality, publishing, and platform context.'
      }
      action={
        product ? (
          <span className="phlo-observatory-pill">
            {product.publication_state}
          </span>
        ) : null
      }
    >
      {profile ? (
        <ProfileContent profile={profile} />
      ) : (
        <div className="phlo-observatory-empty-state">
          {result.error ?? 'Loading Data Product Profile...'}
        </div>
      )}
    </ObservatoryPage>
  )
}

function ProfileContent({
  profile,
}: {
  profile: ObservatoryDataProductProfile
}) {
  const { product } = profile
  return (
    <section className="phlo-observatory-surface-grid">
      <div className="phlo-observatory-list-surface">
        <div className="phlo-observatory-browser-toolbar">
          <span>
            <Boxes className="size-4" />
            Profile sections
          </span>
          <StatusBadge
            label={product.readiness_state}
            state={product.readiness_state}
          />
        </div>
        <div className="phlo-observatory-diff-metrics">
          <Metric
            icon={<Database className="size-5" />}
            label="Tables"
            value={profile.tables.length}
          />
          <Metric
            icon={<ListChecks className="size-5" />}
            label="Checks"
            value={profile.quality.length}
          />
          <Metric
            icon={<GitBranch className="size-5" />}
            label="Lineage"
            value={profile.upstream.length + profile.downstream.length}
          />
          <Metric
            icon={<ShieldCheck className="size-5" />}
            label="Classifications"
            value={product.classifications.length}
          />
        </div>
        <ProfileSection title="Source objects">
          {product.source_refs.map((ref) => (
            <div
              className="phlo-observatory-mini-row"
              key={`${ref.kind}:${ref.id}`}
            >
              <span>{ref.label}</span>
              <small>{ref.kind}</small>
            </div>
          ))}
        </ProfileSection>
        <ProfileSection title="Quality">
          {profile.quality.length ? (
            profile.quality.map((check) => (
              <div className="phlo-observatory-mini-row" key={check.id}>
                <span>{check.name}</span>
                <small>{check.status}</small>
              </div>
            ))
          ) : (
            <EmptyRow label="No quality checks returned" />
          )}
        </ProfileSection>
        <ProfileSection title="Governance">
          {profile.governance.length ? (
            profile.governance.map((control) => (
              <div className="phlo-observatory-mini-row" key={control.id}>
                <span>{control.label}</span>
                <small>{control.status.replace('_', ' ')}</small>
              </div>
            ))
          ) : (
            <EmptyRow label="No governance controls returned" />
          )}
        </ProfileSection>
        <ProfileSection title="Lineage">
          {[...profile.upstream, ...profile.downstream].length ? (
            <>
              {profile.upstream.map((ref) => (
                <div className="phlo-observatory-mini-row" key={`up:${ref.id}`}>
                  <span>{ref.label}</span>
                  <small>upstream</small>
                </div>
              ))}
              {profile.downstream.map((ref) => (
                <div
                  className="phlo-observatory-mini-row"
                  key={`down:${ref.id}`}
                >
                  <span>{ref.label}</span>
                  <small>downstream</small>
                </div>
              ))}
            </>
          ) : (
            <EmptyRow label="No lineage returned" />
          )}
        </ProfileSection>
      </div>

      <aside className="phlo-observatory-inspector">
        <div className="phlo-observatory-inspector-label">Overview</div>
        <h2>{product.name}</h2>
        <p>{product.description ?? 'No description returned.'}</p>
        <dl className="phlo-observatory-facts">
          <Fact
            icon={<UserRound className="size-3.5" />}
            label="Owner"
            value={product.owner ?? 'unassigned'}
          />
          <Fact label="Publication" value={product.publication_state} />
          <Fact label="Readiness" value={product.readiness_state} />
          <Fact
            label="Classification"
            value={
              product.classifications.length
                ? product.classifications.join(', ')
                : 'none'
            }
          />
        </dl>
        <div className="phlo-observatory-detail-list">
          {profile.tables.map((table) => (
            <Link
              className="phlo-observatory-mini-row"
              key={table.id}
              params={{ tableId: table.id }}
              to="/data/$tableId"
            >
              <span>{table.name}</span>
              <small>{table.namespace ?? 'table'}</small>
            </Link>
          ))}
          {profile.tables.length === 0 && <EmptyRow label="No table binding" />}
        </div>
      </aside>
    </section>
  )
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: string | number
}) {
  return (
    <div className="phlo-observatory-command-metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ProfileSection({
  children,
  title,
}: {
  children: ReactNode
  title: string
}) {
  return (
    <div className="phlo-observatory-detail-list phlo-observatory-detail-list-padded">
      <div className="phlo-observatory-mini-row">
        <span>{title}</span>
        <small>profile</small>
      </div>
      {children}
    </div>
  )
}

function Fact({
  icon,
  label,
  value,
}: {
  icon?: ReactNode
  label: string
  value: string
}) {
  return (
    <>
      <dt>
        {icon}
        {label}
      </dt>
      <dd>{value}</dd>
    </>
  )
}

function EmptyRow({ label }: { label: string }) {
  return (
    <div className="phlo-observatory-mini-row">
      <span>{label}</span>
      <small>empty</small>
    </div>
  )
}

import { Link, createFileRoute } from '@tanstack/react-router'
import {
  Boxes,
  CheckCircle2,
  Database,
  GitBranch,
  ListChecks,
  ShieldCheck,
  UserRound,
  UserPlus,
  XCircle,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryDataProductProfile,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import {
  getObservatoryDataProductProfileDirect,
  runObservatoryActionDirect,
} from '@/observatory/api/resources'
import { ActionButton } from '@/observatory/components/ActionButton'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { StatusBadge } from '@/observatory/components/StatusBadge'
import { invalidateCachedResources } from '@/observatory/routes/liveResource'

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

  function refreshProfile() {
    void getObservatoryDataProductProfileDirect({ productId }).then(setResult)
  }

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
        <ProfileContent onRefresh={refreshProfile} profile={profile} />
      ) : (
        <div className="phlo-observatory-empty-state">
          {result.error ?? 'Loading Data Product Profile...'}
        </div>
      )}
    </ObservatoryPage>
  )
}

function ProfileContent({
  onRefresh,
  profile,
}: {
  onRefresh: () => void
  profile: ObservatoryDataProductProfile
}) {
  const { product } = profile
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const onAction = (actionId: string) => {
    setActionMessage('Requesting workflow action...')
    void runObservatoryActionDirect({ actionId }).then((next) => {
      invalidateCachedResources(['v2:data-products', 'v2:operations'])
      setActionMessage(next.data?.message ?? next.error ?? 'Action requested')
      onRefresh()
    })
  }

  return (
    <section className="phlo-observatory-surface-grid">
      <div className="phlo-observatory-list-surface phlo-observatory-product-profile-surface">
        <div className="phlo-observatory-browser-toolbar">
          <span>
            <Boxes className="size-4" />
            Decision summary
          </span>
          <StatusBadge
            label={product.readiness_state}
            state={product.readiness_state}
          />
        </div>
        <ReadinessStrip profile={profile} />
        <div className="phlo-observatory-product-summary">
          <SummaryMetric
            icon={<Database className="size-5" />}
            label="Tables"
            value={profile.tables.length}
            detail={profile.tables[0]?.namespace ?? 'bound sources'}
          />
          <SummaryMetric
            icon={<ListChecks className="size-5" />}
            label="Checks"
            value={profile.quality.length}
            detail={`${product.readiness_state} readiness`}
          />
          <SummaryMetric
            icon={<GitBranch className="size-5" />}
            label="Lineage"
            value={profile.upstream.length + profile.downstream.length}
            detail={`${profile.upstream.length} up · ${profile.downstream.length} down`}
          />
          <SummaryMetric
            icon={<ShieldCheck className="size-5" />}
            label="Classifications"
            value={product.classifications.length}
            detail={
              product.classifications.length
                ? product.classifications.join(', ')
                : 'none declared'
            }
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
        <ProfileSection title="Controls">
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
        <ProfileSection title="Usage">
          <UsageRows profile={profile} />
        </ProfileSection>
        <ProfileSection title="Publication">
          <PublishingRows onAction={onAction} profile={profile} />
        </ProfileSection>
        {product.candidate && (
          <ProfileSection title="Candidate workflow">
            <CandidateWorkflowRows onAction={onAction} profile={profile} />
          </ProfileSection>
        )}
        <ProfileSection title="Pipeline state">
          <PipelineRows profile={profile} />
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
        {actionMessage && (
          <div className="phlo-observatory-panel-footer">{actionMessage}</div>
        )}
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

function PipelineRows({ profile }: { profile: ObservatoryDataProductProfile }) {
  const pipeline = profile.pipeline
  return (
    <>
      <div className="phlo-observatory-mini-row">
        <span>Freshness</span>
        <small>{pipeline.freshness_at ?? pipeline.freshness_state}</small>
      </div>
      <div className="phlo-observatory-mini-row">
        <span>Last run</span>
        <small>{pipeline.last_run?.label ?? 'none'}</small>
      </div>
      {pipeline.stages.map((stage) => (
        <div className="phlo-observatory-mini-row" key={stage.id}>
          <span>{stage.label}</span>
          <small>{stage.state}</small>
        </div>
      ))}
    </>
  )
}

function PublishingRows({
  onAction,
  profile,
}: {
  onAction: (actionId: string) => void
  profile: ObservatoryDataProductProfile
}) {
  const publishing = profile.publishing
  return (
    <>
      <div className="phlo-observatory-mini-row">
        <span>{profile.product.publication_state}</span>
        <small>
          {publishing.policy_name} · {publishing.state}
        </small>
      </div>
      {publishing.blockers.map((blocker) => (
        <div className="phlo-observatory-mini-row" key={`blocker:${blocker}`}>
          <span>{blocker}</span>
          <small>blocker</small>
        </div>
      ))}
      {publishing.missing_evidence.map((item) => (
        <div className="phlo-observatory-mini-row" key={`missing:${item}`}>
          <span>{item}</span>
          <small>missing evidence</small>
        </div>
      ))}
      {publishing.actions.map((action) => (
        <div
          className="phlo-observatory-mini-row"
          key={action.id}
          title={action.consequences.join(' ')}
        >
          <span>{action.label}</span>
          <small>{action.enabled ? 'ready' : action.reason}</small>
        </div>
      ))}
      <div className="phlo-observatory-action-row">
        {publishing.actions.map((action) => (
          <ActionButton
            action={{
              ...action,
              id: `data-product:${profile.product.id}:${action.id}`,
              kind: `data_product.${action.id}`,
              requires_confirmation: true,
              risk_level: action.id === 'retire' ? 'medium' : 'low',
              expected_evidence: [],
            }}
            key={action.id}
            onRun={onAction}
          />
        ))}
      </div>
      <div className="phlo-observatory-mini-row">
        <span>Internal only</span>
        <small>{publishing.internal_only ? 'yes' : 'no'}</small>
      </div>
    </>
  )
}

function CandidateWorkflowRows({
  onAction,
  profile,
}: {
  onAction: (actionId: string) => void
  profile: ObservatoryDataProductProfile
}) {
  const sourceId = profile.product.source_refs[0]?.id ?? profile.product.id
  return (
    <>
      <div className="phlo-observatory-mini-row">
        <span>Claim</span>
        <small>assign one accountable owner before promotion</small>
      </div>
      <div className="phlo-observatory-mini-row">
        <span>Promote</span>
        <small>turn the candidate into a governed Data Product</small>
      </div>
      <div className="phlo-observatory-inline-actions">
        <button
          onClick={() => onAction(`candidate:${sourceId}:claim`)}
          type="button"
        >
          <UserPlus className="size-3.5" />
          Claim
        </button>
        <button
          onClick={() => onAction(`candidate:${sourceId}:promote`)}
          type="button"
        >
          <CheckCircle2 className="size-3.5" />
          Promote
        </button>
        <button
          onClick={() => onAction(`candidate:${sourceId}:reject`)}
          type="button"
        >
          <XCircle className="size-3.5" />
          Reject
        </button>
      </div>
    </>
  )
}

function UsageRows({ profile }: { profile: ObservatoryDataProductProfile }) {
  const usage = profile.usage
  const gaps = [
    usage.access_activity.length ? null : 'access activity',
    usage.dependency_activity.length ? null : 'dependency activity',
    usage.consumer_adoption.length ? null : 'consumer adoption',
  ].filter((gap): gap is string => Boolean(gap))
  return (
    <>
      <div className="phlo-observatory-mini-row">
        <span>Access Activity</span>
        <small>{usage.access_activity.length}</small>
      </div>
      {usage.access_activity.slice(0, 4).map((activity) => (
        <div className="phlo-observatory-mini-row" key={activity.id}>
          <span>{activity.action}</span>
          <small>
            {activity.actor_label ?? 'access'} · {activity.count}
          </small>
        </div>
      ))}
      <div className="phlo-observatory-mini-row">
        <span>Dependency Activity</span>
        <small>{usage.dependency_activity.length}</small>
      </div>
      {usage.dependency_activity.slice(0, 4).map((activity) => (
        <div className="phlo-observatory-mini-row" key={activity.id}>
          <span>{activity.source.label}</span>
          <small>{activity.kind}</small>
        </div>
      ))}
      <div className="phlo-observatory-mini-row">
        <span>Consumer Adoption</span>
        <small>{usage.consumer_adoption.length}</small>
      </div>
      {usage.consumer_adoption.slice(0, 4).map((consumer) => (
        <div className="phlo-observatory-mini-row" key={consumer.id}>
          <span>{consumer.consumer}</span>
          <small>
            {consumer.kind} · {consumer.status}
          </small>
        </div>
      ))}
      <div className="phlo-observatory-mini-row">
        <span>Privacy</span>
        <small>{usage.privacy_policy.identity_detail.replace('_', ' ')}</small>
      </div>
      <div className="phlo-observatory-mini-row">
        <span>Telemetry gaps</span>
        <small>{gaps.length ? gaps.join(', ') : 'none'}</small>
      </div>
    </>
  )
}

function ReadinessStrip({
  profile,
}: {
  profile: ObservatoryDataProductProfile
}) {
  const { product, publishing } = profile
  const nextAction =
    publishing.actions.find((action) => action.enabled) ??
    publishing.actions[0] ??
    null
  return (
    <div className="phlo-observatory-product-decision-strip">
      <DecisionFact
        label="Owner"
        value={product.owner ?? 'Needs owner'}
        tone={product.owner ? 'ok' : 'warning'}
      />
      <DecisionFact
        label="Publication"
        value={product.publication_state}
        tone={publishing.blockers.length ? 'warning' : 'ok'}
      />
      <DecisionFact
        label="Blockers"
        value={publishing.blockers.length}
        tone={publishing.blockers.length ? 'error' : 'ok'}
      />
      <DecisionFact
        label="Next action"
        value={
          nextAction?.enabled
            ? nextAction.label
            : (nextAction?.reason ?? 'No action available')
        }
        tone={nextAction?.enabled ? 'ok' : 'warning'}
      />
    </div>
  )
}

function DecisionFact({
  label,
  tone,
  value,
}: {
  label: string
  tone: 'ok' | 'warning' | 'error'
  value: string | number
}) {
  return (
    <div className="phlo-observatory-product-decision-fact" data-state={tone}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function SummaryMetric({
  detail,
  icon,
  label,
  value,
}: {
  detail: string
  icon: ReactNode
  label: string
  value: string | number
}) {
  return (
    <div className="phlo-observatory-product-summary-item">
      {icon}
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
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
    <section className="phlo-observatory-product-profile-section">
      <div className="phlo-observatory-product-profile-section-title">
        {title}
      </div>
      {children}
    </section>
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

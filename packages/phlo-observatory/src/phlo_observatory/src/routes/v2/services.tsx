import { createFileRoute } from '@tanstack/react-router'
import { ExternalLink, Play, RotateCcw, Server, Square } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import type {
  V2ResourceResult,
  V2Service,
  V2ServiceDetail,
} from '@/v2/api/types'
import { getV2ServiceDetail, getV2Services } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/services')({
  component: Services,
})

function Services() {
  const result = useLiveResource(getV2Services)
  const services = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    services.find((service) => service.id === selectedId) ?? services[0] ?? null
  const [detail, setDetail] = useState<V2ResourceResult<V2ServiceDetail>>({
    data: null,
    error: null,
  })
  const counts = useMemo(
    () => ({
      running: services.filter((service) => service.status === 'running')
        .length,
      attention: services.filter(
        (service) =>
          service.status === 'stopped' ||
          service.status === 'unhealthy' ||
          service.health.state === 'warning' ||
          service.health.state === 'error',
      ).length,
      total: services.length,
    }),
    [services],
  )

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getV2ServiceDetail({ data: { serviceId: selected.id } }).then(
      (next) => {
        if (!cancelled) setDetail(next)
      },
    )
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <V2Page
      kicker="Services"
      title="Service hub"
      description="Runtime status, impact, links, and guarded service actions."
      action={<span className="phlo-v2-pill">{counts.total} services</span>}
    >
      <section className="phlo-v2-diff-metrics">
        <Metric label="Running" value={counts.running} />
        <Metric label="Needs Attention" value={counts.attention} />
        <Metric label="Registered" value={counts.total} />
      </section>
      <section className="phlo-v2-services-workbench">
        <div className="phlo-v2-service-list">
          {services.map((service) => (
            <button
              className="phlo-v2-service-row"
              data-active={service.id === selected?.id}
              key={service.id}
              onClick={() => setSelectedId(service.id)}
              type="button"
            >
              <span className="phlo-v2-dot" data-state={service.status} />
              <span>{service.name}</span>
              <small>{service.kind}</small>
              <strong>{service.status}</strong>
            </button>
          ))}
        </div>
        <aside className="phlo-v2-service-detail">
          {selected ? (
            <ServiceDetail detail={detail.data} service={selected} />
          ) : (
            <p>No services returned yet.</p>
          )}
          {detail.error && (
            <div className="phlo-v2-panel-footer">{detail.error}</div>
          )}
          {result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
  )
}

function ServiceDetail({
  detail,
  service,
}: {
  detail: V2ServiceDetail | null
  service: V2Service
}) {
  const actions = detail?.actions ?? []
  return (
    <>
      <div className="phlo-v2-detail-header">
        <span>{service.kind}</span>
        <h2>{service.name}</h2>
        <p>{service.health.message ?? 'No runtime health message returned.'}</p>
      </div>
      <dl className="phlo-v2-facts">
        <Fact label="Status" value={service.status} />
        <Fact label="Health" value={service.health.state} />
        <Fact
          label="Depends on"
          value={service.depends_on.join(', ') || 'none'}
        />
        <Fact label="Impacts" value={service.impacts.join(', ') || 'none'} />
      </dl>
      <div className="phlo-v2-action-row">
        {(actions.length ? actions : fallbackActions(service.id)).map(
          (action) => (
            <button
              disabled={!action.enabled}
              key={action.id}
              title={action.reason ?? undefined}
              type="button"
            >
              {iconForAction(action.kind)}
              {action.label}
            </button>
          ),
        )}
      </div>
      <div className="phlo-v2-detail-list">
        <div className="phlo-v2-mini-row">
          <span>Dependencies</span>
          <small>
            {detail?.dependencies.map((item) => item.name).join(', ') || 'none'}
          </small>
        </div>
        <div className="phlo-v2-mini-row">
          <span>Dependents</span>
          <small>
            {detail?.dependents.map((item) => item.name).join(', ') || 'none'}
          </small>
        </div>
        <div className="phlo-v2-mini-row">
          <span>Logs</span>
          <small>{detail?.logs.length ?? 0} linked events</small>
        </div>
      </div>
      <div className="phlo-v2-chip-cloud">
        {service.links.map((link) => (
          <a
            className="phlo-v2-chip"
            href={link.url}
            key={`${link.kind}:${link.label}`}
          >
            <ExternalLink className="size-3" />
            {link.label}
          </a>
        ))}
        {service.links.length === 0 && (
          <span className="phlo-v2-chip">
            <Server className="size-3" />
            No links exposed
          </span>
        )}
      </div>
    </>
  )
}

function fallbackActions(serviceId: string) {
  return [
    {
      id: `${serviceId}:start`,
      kind: 'service.start',
      label: 'Start',
      enabled: false,
      reason: 'Action contract not loaded.',
    },
    {
      id: `${serviceId}:stop`,
      kind: 'service.stop',
      label: 'Stop',
      enabled: false,
      reason: 'Action contract not loaded.',
    },
    {
      id: `${serviceId}:restart`,
      kind: 'service.restart',
      label: 'Restart',
      enabled: false,
      reason: 'Action contract not loaded.',
    },
  ]
}

function iconForAction(kind: string) {
  if (kind.endsWith('stop')) return <Square className="size-3.5" />
  if (kind.endsWith('restart')) return <RotateCcw className="size-3.5" />
  return <Play className="size-3.5" />
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="phlo-v2-diff-metric">
      <Server className="size-5" />
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

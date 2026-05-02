import { createFileRoute } from '@tanstack/react-router'
import {
  ExternalLink,
  Layers3,
  Package,
  Play,
  RotateCcw,
  Server,
  Square,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2ResourceResult,
  V2Service,
  V2ServiceDetail,
} from '@/v2/api/types'
import {
  getV2ServiceDetail,
  getV2Services,
  runV2Action,
} from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { loadCachedResource, useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/services')({
  component: Services,
})

function Services() {
  const result = useLiveResource(getV2Services, 120_000, 'v2:services')
  const services = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const runtimeServices = useMemo(
    () => services.filter((service) => isRuntimeService(service)),
    [services],
  )
  const availableServices = useMemo(
    () => services.filter((service) => !isRuntimeService(service)),
    [services],
  )
  const availableSections = useMemo(
    () => groupServicesByKind(availableServices),
    [availableServices],
  )
  const selected =
    services.find((service) => service.id === selectedId) ??
    runtimeServices.find((service) => service.status === 'running') ??
    runtimeServices[0] ??
    services[0] ??
    null
  const [detail, setDetail] = useState<V2ResourceResult<V2ServiceDetail>>({
    data: null,
    error: null,
  })
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const counts = useMemo(
    () => ({
      running: runtimeServices.filter((service) => service.status === 'running')
        .length,
      attention: runtimeServices.filter(
        (service) =>
          service.status === 'unhealthy' ||
          service.health.state === 'warning' ||
          service.health.state === 'error' ||
          (service.status === 'stopped' && service.health.state !== 'ok'),
      ).length,
      runtime: runtimeServices.length,
      available: availableServices.length,
    }),
    [availableServices.length, runtimeServices, services],
  )

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void loadCachedResource(
      `v2:service-detail:${selected.id}`,
      () => getV2ServiceDetail({ data: { serviceId: selected.id } }),
      { staleMs: 120_000 },
    ).then((next) => {
      if (!cancelled) setDetail(next)
    })
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <V2Page
      kicker="Services"
      title="Runtime services"
      description="Inspect the running stack first; browse optional service definitions when you need to add capability."
      action={<span className="phlo-v2-pill">{counts.runtime} in stack</span>}
    >
      <section className="phlo-v2-diff-metrics">
        <Metric label="Running" value={counts.running} />
        <Metric label="Needs Attention" value={counts.attention} />
        <Metric label="Available Definitions" value={counts.available} />
      </section>
      <section className="phlo-v2-services-workbench">
        <div className="phlo-v2-service-directory">
          <ServiceSection
            countLabel={`${runtimeServices.length} services`}
            icon={<Server className="size-4" />}
            onSelect={setSelectedId}
            selectedId={selected?.id}
            services={runtimeServices}
            title="Runtime stack"
          />
          <section className="phlo-v2-service-section phlo-v2-service-definitions">
            <div className="phlo-v2-browser-toolbar">
              <span>
                <Package className="size-4" />
                Available definitions
              </span>
              <span className="phlo-v2-pill">
                {availableServices.length} optional
              </span>
            </div>
            <p className="phlo-v2-section-note">
              These are service definitions Observatory can describe. They are
              not running in this lakehouse until added to the stack.
            </p>
            <div className="phlo-v2-service-category-grid">
              {availableSections.map((section) => (
                <ServiceSection
                  compact
                  countLabel={`${section.services.length}`}
                  icon={<Layers3 className="size-4" />}
                  key={section.kind}
                  onSelect={setSelectedId}
                  selectedId={selected?.id}
                  services={section.services}
                  title={labelize(section.kind)}
                />
              ))}
            </div>
          </section>
        </div>
        <aside className="phlo-v2-service-detail">
          {selected ? (
            <ServiceDetail
              detail={detail.data}
              onAction={(actionId) => {
                if (
                  !window.confirm(
                    `Run ${actionId}? This will call phlo-api to change a local service.`,
                  )
                ) {
                  return
                }
                setActionMessage('Running action...')
                void runV2Action({ data: { actionId } }).then((next) => {
                  setActionMessage(
                    next.data?.message ?? next.error ?? 'Action completed',
                  )
                })
              }}
              runtime={isRuntimeService(selected)}
              service={selected}
            />
          ) : (
            <p>No services returned yet.</p>
          )}
          {actionMessage && (
            <div className="phlo-v2-panel-footer">{actionMessage}</div>
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
  onAction,
  runtime,
  service,
}: {
  detail: V2ServiceDetail | null
  onAction: (actionId: string) => void
  runtime: boolean
  service: V2Service
}) {
  const actions = runtime ? (detail?.actions ?? []) : []
  return (
    <>
      <div className="phlo-v2-detail-header">
        <span>{service.kind}</span>
        <h2>{service.name}</h2>
        <p>
          {runtime
            ? (service.health.message ?? 'No runtime health message returned.')
            : 'Available definition. Not part of the current runtime stack.'}
        </p>
      </div>
      <dl className="phlo-v2-facts">
        <Fact label="Status" value={runtime ? service.status : 'available'} />
        <Fact label="Health" value={runtime ? service.health.state : 'n/a'} />
        <Fact
          label="Depends on"
          value={service.depends_on.join(', ') || 'none'}
        />
        <Fact label="Impacts" value={service.impacts.join(', ') || 'none'} />
      </dl>
      {actions.length > 0 && (
        <div className="phlo-v2-action-row">
          {actions.map((action) => (
            <button
              disabled={!action.enabled}
              key={action.id}
              onClick={() => onAction(action.id)}
              title={action.reason ?? undefined}
              type="button"
            >
              {iconForAction(action.kind)}
              {action.label}
            </button>
          ))}
        </div>
      )}
      <div className="phlo-v2-detail-list">
        <div className="phlo-v2-mini-row">
          <span>Safe actions</span>
          <small>
            {actions.length
              ? `${actions.filter((action) => action.enabled).length} enabled`
              : 'No action contract exposed'}
          </small>
        </div>
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
          <span>Ports</span>
          <small>
            {detail?.ports
              .map((port) =>
                [port.published, port.target].filter(Boolean).join(' -> '),
              )
              .join(', ') || 'none'}
          </small>
        </div>
        <div className="phlo-v2-mini-row">
          <span>Config</span>
          <small>{detail?.config.length ?? 0} entries</small>
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

function ServiceSection({
  compact = false,
  countLabel,
  icon,
  onSelect,
  selectedId,
  services,
  title,
}: {
  compact?: boolean
  countLabel: string
  icon: ReactNode
  onSelect: (id: string) => void
  selectedId?: string | null
  services: Array<V2Service>
  title: string
}) {
  return (
    <section className="phlo-v2-service-section" data-compact={compact}>
      <div className="phlo-v2-browser-toolbar">
        <span>
          {icon}
          {title}
        </span>
        <span className="phlo-v2-pill">{countLabel}</span>
      </div>
      <div className="phlo-v2-service-list">
        {services.map((service) => (
          <button
            className="phlo-v2-service-row"
            data-active={service.id === selectedId}
            key={service.id}
            onClick={() => onSelect(service.id)}
            type="button"
          >
            <span
              className="phlo-v2-dot"
              data-state={serviceDotState(service)}
            />
            <span>{service.name}</span>
            <small>{service.kind}</small>
            <strong>{serviceStatusLabel(service)}</strong>
          </button>
        ))}
        {services.length === 0 && (
          <div className="phlo-v2-empty-state">No services in this group.</div>
        )}
      </div>
    </section>
  )
}

function groupServicesByKind(services: Array<V2Service>): Array<{
  kind: string
  services: Array<V2Service>
}> {
  const groups = new Map<string, Array<V2Service>>()
  for (const service of services) {
    const kind = service.kind || 'other'
    groups.set(kind, [...(groups.get(kind) ?? []), service])
  }
  return Array.from(groups.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([kind, kindServices]) => ({ kind, services: kindServices }))
}

function isRuntimeService(service: V2Service): boolean {
  if (typeof service.in_stack === 'boolean') return service.in_stack
  return (
    service.status !== 'unknown' ||
    service.health.state !== 'unknown' ||
    service.health.message !== 'Runtime status unavailable'
  )
}

function serviceStatusLabel(service: V2Service): string {
  if (!isRuntimeService(service)) return 'available'
  if (service.status === 'stopped' && service.health.state === 'ok') {
    return 'completed'
  }
  return service.status
}

function serviceDotState(service: V2Service): string {
  if (service.status === 'stopped' && service.health.state === 'ok') {
    return 'ok'
  }
  return service.status
}

function labelize(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
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

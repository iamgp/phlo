import {
  Activity,
  AlertCircle,
  Boxes,
  CheckCircle2,
  Clock3,
  Database,
  Server,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { V2Overview, V2ResourceResult, V2Service } from '@/v2/api/types'
import { getV2Overview, getV2Services } from '@/v2/api/resources'
import { StatusBadge } from '@/v2/components/StatusBadge'

const formatter = new Intl.NumberFormat('en')

export function OverviewRoute() {
  const [overview, setOverview] = useState<V2ResourceResult<V2Overview>>({
    data: null,
    error: null,
  })
  const [services, setServices] = useState<V2ResourceResult<Array<V2Service>>>({
    data: null,
    error: null,
  })
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      const [nextOverview, nextServices] = await Promise.all([
        getV2Overview(),
        getV2Services(),
      ])

      if (!cancelled) {
        setOverview(nextOverview)
        setServices(nextServices)
        setUpdatedAt(new Date())
      }
    }

    void load()
    const interval = window.setInterval(load, 15_000)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  const serviceRows = services.data ?? []
  const counters = overview.data?.counters ?? {}
  const runningServices = useMemo(
    () => serviceRows.filter((service) => service.status === 'running').length,
    [serviceRows],
  )
  const attentionServices = useMemo(
    () =>
      serviceRows.filter(
        (service) =>
          service.status === 'stopped' ||
          service.status === 'unhealthy' ||
          service.health.state === 'error' ||
          service.health.state === 'warning',
      ).length,
    [serviceRows],
  )
  const apiError = overview.error ?? services.error

  return (
    <div className="phlo-v2-content">
      <header className="phlo-v2-section-header">
        <div>
          <div className="phlo-v2-kicker">Lakehouse control plane</div>
          <h1 className="phlo-v2-title">Your lakehouse, ready to operate.</h1>
          <p className="phlo-v2-subtitle">
            Monitor platform health, understand service impact, and take the
            next operational step from one calm workspace.
          </p>
        </div>
        <StatusBadge
          label={overview.data?.health.message ?? 'API pending'}
          state={
            overview.data?.health.state ?? (apiError ? 'warning' : 'unknown')
          }
        />
      </header>

      <section className="phlo-v2-grid" aria-label="Platform counters">
        <MetricTile
          icon={<Server className="size-4" />}
          label="Services"
          note={`${formatter.format(runningServices)} running`}
          value={counterValue(counters.services, serviceRows.length)}
        />
        <MetricTile
          icon={<AlertCircle className="size-4" />}
          label="Needs Attention"
          note="Service or health warnings"
          value={counterValue(counters.incidents, attentionServices)}
        />
        <MetricTile
          icon={<Boxes className="size-4" />}
          label="Assets"
          note="Provider-neutral resource count"
          value={counterValue(counters.assets)}
        />
        <MetricTile
          icon={<Database className="size-4" />}
          label="Tables"
          note="Available through phlo-api"
          value={counterValue(counters.tables)}
        />
      </section>

      <section className="phlo-v2-split">
        <div className="phlo-v2-panel">
          <div className="phlo-v2-panel-header">
            <h2 className="phlo-v2-panel-title">Services</h2>
            <span className="phlo-v2-pill">
              <Activity className="size-3.5" />
              {serviceRows.length ? 'Live from phlo-api' : 'Waiting'}
            </span>
          </div>
          <div className="phlo-v2-list">
            {serviceRows.length > 0 ? (
              serviceRows.map((service) => (
                <ServiceRow key={service.id} service={service} />
              ))
            ) : (
              <EmptyRow label="No services returned yet" />
            )}
          </div>
        </div>

        <aside>
          <div className="phlo-v2-callout">
            <div className="phlo-v2-callout-title">
              <CheckCircle2 className="size-4" />
              Operator view
            </div>
            <p className="phlo-v2-callout-body">
              Service relationships, status, and impact signals are gathered
              into one place so recovery work starts with context.
            </p>
          </div>

          <div className="phlo-v2-callout">
            <div className="phlo-v2-callout-title">
              <Clock3 className="size-4" />
              Refresh cadence
            </div>
            <p className="phlo-v2-callout-body">
              {updatedAt
                ? `Last refreshed ${updatedAt.toLocaleTimeString()}`
                : 'Loading the first snapshot'}
            </p>
          </div>

          {apiError && (
            <div className="phlo-v2-callout">
              <div className="phlo-v2-callout-title">
                <AlertCircle className="size-4" />
                API not ready
              </div>
              <p className="phlo-v2-callout-body">{apiError}</p>
            </div>
          )}
        </aside>
      </section>
    </div>
  )
}

function MetricTile({
  icon,
  label,
  note,
  value,
}: {
  icon: ReactNode
  label: string
  note: string
  value: string
}) {
  return (
    <div className="phlo-v2-tile">
      <div className="phlo-v2-tile-label">
        <span>{label}</span>
        {icon}
      </div>
      <div className="phlo-v2-tile-value">{value}</div>
      <div className="phlo-v2-tile-note">{note}</div>
    </div>
  )
}

function ServiceRow({ service }: { service: V2Service }) {
  const dependencyText =
    service.depends_on.length > 0
      ? `Depends on ${service.depends_on.join(', ')}`
      : 'No declared dependencies'

  return (
    <div className="phlo-v2-row">
      <div className="phlo-v2-row-main">
        <div className="phlo-v2-row-title">
          <span className="phlo-v2-dot" data-state={service.status} />
          <span>{service.name}</span>
        </div>
        <div className="phlo-v2-row-meta">
          {service.kind} · {dependencyText}
        </div>
      </div>
      <StatusBadge label={service.status} state={service.status} />
    </div>
  )
}

function EmptyRow({ label }: { label: string }) {
  return (
    <div className="phlo-v2-row">
      <div className="phlo-v2-row-main">
        <div className="phlo-v2-row-title">{label}</div>
        <div className="phlo-v2-row-meta">
          Start phlo-api or add v2 resources to populate this surface.
        </div>
      </div>
    </div>
  )
}

function counterValue(primary?: number, fallback?: number): string {
  const value = primary ?? fallback
  return typeof value === 'number' ? formatter.format(value) : '--'
}

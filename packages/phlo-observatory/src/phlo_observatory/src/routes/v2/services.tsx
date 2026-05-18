import { createFileRoute } from '@tanstack/react-router'
import {
  Download,
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
  getV2ServiceDetailDirect,
  getV2Services,
  getV2ServicesDirect,
  installV2Package,
  installV2PackageDirect,
  runV2Action,
  runV2ActionDirect,
} from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import {
  invalidateCachedResources,
  loadCachedResource,
  useLiveResource,
} from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/services')({
  component: Services,
})

type ServicePackageGroup = {
  id: string
  name: string
  kind: string
  packageName: string | null
  primary: V2Service
  services: Array<V2Service>
  inStack: boolean
  installable: boolean
}

export function Services() {
  const result = useLiveResource(getV2Services, 120_000, 'v2:services')
  const [directResult, setDirectResult] = useState<V2ResourceResult<
    Array<V2Service>
  > | null>(null)
  const services = result.data ?? directResult?.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const serviceGroups = useMemo(
    () => groupServicesByPackage(services),
    [services],
  )
  const runtimeServiceGroups = useMemo(
    () => serviceGroups.filter((group) => group.inStack),
    [serviceGroups],
  )
  const availableServiceGroups = useMemo(
    () => serviceGroups.filter((group) => !group.inStack),
    [serviceGroups],
  )
  const availableSections = useMemo(
    () => groupServicePackagesByKind(availableServiceGroups),
    [availableServiceGroups],
  )
  const selected =
    serviceGroups.find((group) => group.id === selectedId) ??
    runtimeServiceGroups.find((group) => group.primary.status === 'running') ??
    runtimeServiceGroups[0] ??
    serviceGroups[0] ??
    null
  const selectedService = selected?.primary ?? null
  const runtimeServices = useMemo(
    () => runtimeServiceGroups.flatMap((group) => group.services),
    [runtimeServiceGroups],
  )
  const [detail, setDetail] = useState<V2ResourceResult<V2ServiceDetail>>({
    data: null,
    error: null,
  })
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  useEffect(() => {
    if (result.data || directResult) return
    let cancelled = false
    void getV2ServicesDirect().then((next) => {
      if (!cancelled) setDirectResult(next)
    })
    return () => {
      cancelled = true
    }
  }, [directResult, result.data])
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
      runtime: runtimeServiceGroups.length,
      available: availableServiceGroups.length,
    }),
    [
      availableServiceGroups.length,
      runtimeServiceGroups.length,
      runtimeServices,
    ],
  )

  useEffect(() => {
    if (!selectedService) return
    let cancelled = false
    void loadCachedResource(
      `v2:service-detail:${selectedService.id}`,
      async () => {
        const directResponse = await getV2ServiceDetailDirect({
          serviceId: selectedService.id,
        })
        if (directResponse.data || !directResponse.error) return directResponse
        const response = await getV2ServiceDetail({
          data: { serviceId: selectedService.id },
        }).catch((error: unknown) => ({
          data: null,
          error:
            error instanceof Error
              ? error.message
              : 'Lakehouse API is unavailable',
        }))
        if (response.data || !response.error) return response
        return directResponse
      },
      { staleMs: 120_000 },
    ).then((next) => {
      if (!cancelled) setDetail(next)
    })
    return () => {
      cancelled = true
    }
  }, [selectedService])

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
            countLabel={`${runtimeServiceGroups.length} packages`}
            icon={<Server className="size-4" />}
            onSelect={setSelectedId}
            selectedId={selected?.id}
            services={runtimeServiceGroups}
            title="Runtime stack"
          />
          <section className="phlo-v2-service-section phlo-v2-service-definitions">
            <div className="phlo-v2-browser-toolbar">
              <span>
                <Package className="size-4" />
                Available definitions
              </span>
              <span className="phlo-v2-pill">
                {availableServiceGroups.length} optional
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
              group={selected}
              onAction={(actionId, confirmationMessage) => {
                if (
                  !window.confirm(
                    confirmationMessage ??
                      `Run ${actionId}? This will call phlo-api to change a local service.`,
                  )
                ) {
                  return
                }
                setActionMessage('Running action...')
                void runV2ActionDirect({ actionId }).then(async (next) => {
                  if (!next.data && next.error) {
                    next = await runV2Action({ data: { actionId } }).catch(
                      (error: unknown) => ({
                        data: null,
                        error:
                          error instanceof Error
                            ? error.message
                            : 'Action failed',
                      }),
                    )
                  }
                  invalidateCachedResources(['v2:operations', 'v2:services'])
                  setActionMessage(
                    next.data?.message ?? next.error ?? 'Action completed',
                  )
                })
              }}
              onInstall={(packageName) => {
                if (
                  !window.confirm(
                    `Install ${packageName}? This will modify the Python environment used by phlo-api.`,
                  )
                ) {
                  return
                }
                setActionMessage(`Installing ${packageName}...`)
                void installV2PackageDirect({ packageName }).then(
                  async (next) => {
                    if (!next.data && next.error) {
                      next = await installV2Package({
                        data: { packageName },
                      }).catch((error: unknown) => ({
                        data: null,
                        error:
                          error instanceof Error
                            ? error.message
                            : 'Install failed',
                      }))
                    }
                    invalidateCachedResources([
                      'v2:capabilities',
                      'v2:operations',
                      'v2:services',
                    ])
                    setActionMessage(
                      next.data?.message ?? next.error ?? 'Install completed',
                    )
                  },
                )
              }}
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
          {services.length === 0 && result.error && (
            <div className="phlo-v2-panel-footer">{result.error}</div>
          )}
          {!result.error && directResult?.error && (
            <div className="phlo-v2-panel-footer">{directResult.error}</div>
          )}
        </aside>
      </section>
    </V2Page>
  )
}

function ServiceDetail({
  detail,
  group,
  onAction,
  onInstall,
}: {
  detail: V2ServiceDetail | null
  group: ServicePackageGroup
  onAction: (actionId: string, confirmationMessage?: string) => void
  onInstall: (packageName: string) => void
}) {
  const { primary: service } = group
  const actions = serviceActionsForDetail(group, detail)
  const addActionId = `${service.id}:add`
  const packageInstalled = service.metadata.package_installed !== false
  const canAddToStack = !group.inStack && packageInstalled
  const canInstallPackage = !packageInstalled && Boolean(group.packageName)
  const visibleActions = canAddToStack
    ? actions.filter((action) => action.id !== addActionId)
    : actions
  const servicesAddedWithPrimary = addableDependencyNames(group, detail)
  const addImpactMessage =
    servicesAddedWithPrimary.length > 0
      ? `Adding ${group.name} will also add ${formatHumanList(servicesAddedWithPrimary)}.`
      : `Adding ${group.name} will only add ${group.name}.`
  const addConfirmationMessage = `${addImpactMessage}\n\nContinue?`
  const description =
    typeof service.metadata.description === 'string'
      ? service.metadata.description
      : null
  return (
    <>
      <div className="phlo-v2-detail-header">
        <span>{group.packageName ?? service.kind}</span>
        <h2>{group.name}</h2>
        <p>
          {group.inStack
            ? (service.health.message ?? 'No runtime health message returned.')
            : packageInstalled
              ? (description ??
                'This service package is installed and ready to add to this stack.')
              : (description ??
                'Install this package, then add it to this stack.')}
        </p>
      </div>
      <dl className="phlo-v2-facts">
        <Fact
          label="Status"
          value={group.inStack ? service.status : 'available'}
        />
        <Fact
          label="Health"
          value={group.inStack ? service.health.state : 'n/a'}
        />
        <Fact label="Package" value={group.packageName ?? 'unknown'} />
        <Fact
          label="Included services"
          value={group.services.map((item) => item.name).join(', ') || 'none'}
        />
      </dl>
      {canAddToStack && (
        <div className="phlo-v2-service-impact">
          <span>Stack impact</span>
          <strong>{addImpactMessage}</strong>
        </div>
      )}
      {(actions.length > 0 || canAddToStack || canInstallPackage) && (
        <div className="phlo-v2-action-row">
          {canAddToStack && (
            <button
              onClick={() => onAction(addActionId, addConfirmationMessage)}
              type="button"
            >
              <Play className="size-3.5" />
              Add to stack
            </button>
          )}
          {canInstallPackage && group.packageName && (
            <button onClick={() => onInstall(group.packageName!)} type="button">
              <Download className="size-3.5" />
              Install package
            </button>
          )}
          {visibleActions.map((action) => (
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
            {visibleActions.length || canAddToStack
              ? `${
                  visibleActions.filter((action) => action.enabled).length +
                  (canAddToStack ? 1 : 0)
                } enabled`
              : 'No actions available'}
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
  services: Array<ServicePackageGroup>
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
            <small>
              {service.packageName ?? service.kind}
              {service.services.length > 1
                ? ` · ${service.services.length} services`
                : ''}
            </small>
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

function addableDependencyNames(
  group: ServicePackageGroup,
  detail: V2ServiceDetail | null,
): Array<string> {
  const dependencyNames = new Set<string>()
  for (const dependency of detail?.dependencies ?? []) {
    if (dependency.in_stack || dependency.id === group.primary.id) continue
    dependencyNames.add(dependency.name)
  }
  return Array.from(dependencyNames).sort((left, right) =>
    left.localeCompare(right),
  )
}

function formatHumanList(items: Array<string>): string {
  if (items.length <= 1) return items[0] ?? ''
  if (items.length === 2) return `${items[0]} and ${items[1]}`
  return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`
}

function serviceActionsForDetail(
  group: ServicePackageGroup,
  detail: V2ServiceDetail | null,
) {
  const actions = detail?.actions ?? []
  if (
    group.inStack ||
    actions.some((action) => action.id === `${group.primary.id}:add`)
  ) {
    return actions
  }
  const packageInstalled = group.primary.metadata.package_installed !== false
  return [
    ...actions,
    {
      id: `${group.primary.id}:add`,
      label: 'Add to stack',
      kind: 'service.add',
      enabled: packageInstalled,
      requires_confirmation: true,
      reason: packageInstalled
        ? null
        : `Install ${group.packageName ?? group.primary.name} before adding it to the stack.`,
      risk_level: 'low' as const,
      required_capability: null,
      required_service: null,
      required_permission: null,
      equivalent_cli_command: `phlo services add ${group.primary.id}`,
      expected_evidence: [],
      background_operation_id: null,
    },
  ]
}

function groupServicePackagesByKind(
  services: Array<ServicePackageGroup>,
): Array<{
  kind: string
  services: Array<ServicePackageGroup>
}> {
  const groups = new Map<string, Array<ServicePackageGroup>>()
  for (const service of services) {
    const kind = service.kind || 'other'
    groups.set(kind, [...(groups.get(kind) ?? []), service])
  }
  return Array.from(groups.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([kind, kindServices]) => ({ kind, services: kindServices }))
}

function groupServicesByPackage(
  services: Array<V2Service>,
): Array<ServicePackageGroup> {
  const groups = new Map<string, Array<V2Service>>()
  for (const service of services) {
    const key = servicePackageKey(service)
    groups.set(key, [...(groups.get(key) ?? []), service])
  }

  return Array.from(groups.entries())
    .map(([key, groupServices]) => servicePackageGroup(key, groupServices))
    .sort((left, right) => left.name.localeCompare(right.name))
}

function servicePackageGroup(
  key: string,
  services: Array<V2Service>,
): ServicePackageGroup {
  const primary = primaryServiceForPackage(key, services)
  const packageName = servicePackageName(primary)
  return {
    id: key,
    name: serviceDisplayName(primary, packageName),
    kind: primary.kind || 'service',
    packageName,
    primary,
    services: services
      .slice()
      .sort((left, right) => left.name.localeCompare(right.name)),
    inStack: services.some((service) => isRuntimeService(service)),
    installable: services.some(
      (service) => service.metadata.installable === true,
    ),
  }
}

function primaryServiceForPackage(
  key: string,
  services: Array<V2Service>,
): V2Service {
  const packageLabel = key.startsWith('package:')
    ? key.slice('package:'.length).replace(/^phlo-/, '')
    : key
  return (
    services.find((service) => service.name === packageLabel) ??
    services.find((service) => service.id === packageLabel) ??
    services.find(
      (service) => service.metadata.registry_name === packageLabel,
    ) ??
    services
      .slice()
      .sort((left, right) => left.name.length - right.name.length)[0]
  )
}

function servicePackageKey(service: V2Service): string {
  const packageName = servicePackageName(service)
  if (packageName) return `package:${packageName}`
  return `service:${service.id}`
}

function servicePackageName(service: V2Service): string | null {
  return typeof service.metadata.package === 'string'
    ? service.metadata.package
    : null
}

function serviceDisplayName(
  service: V2Service,
  packageName: string | null,
): string {
  if (!packageName) return service.name
  const packageLabel = packageName.replace(/^phlo-/, '')
  if (service.name === packageLabel || service.id === packageLabel) {
    return service.name
  }
  return packageLabel
}

function isRuntimeService(service: V2Service): boolean {
  if (typeof service.in_stack === 'boolean') return service.in_stack
  return (
    service.status !== 'unknown' ||
    service.health.state !== 'unknown' ||
    service.health.message !== 'Runtime status unavailable'
  )
}

function serviceStatusLabel(service: ServicePackageGroup): string {
  if (!service.inStack) {
    return service.installable ? 'not installed' : 'available'
  }
  const primary = service.primary
  if (primary.status === 'stopped' && primary.health.state === 'ok') {
    return 'completed'
  }
  return primary.status
}

function serviceDotState(service: ServicePackageGroup): string {
  if (!service.inStack) return service.installable ? 'unknown' : 'stopped'
  const primary = service.primary
  if (primary.status === 'stopped' && primary.health.state === 'ok') {
    return 'ok'
  }
  return primary.status
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

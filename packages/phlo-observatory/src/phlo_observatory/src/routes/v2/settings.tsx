import { createFileRoute } from '@tanstack/react-router'
import {
  Database,
  Gauge,
  KeyRound,
  RefreshCw,
  RotateCcw,
  Save,
  Settings,
  SlidersHorizontal,
  Wifi,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { useObservatoryExtensions } from '@/extensions/registry'
import type { ObservatorySettings } from '@/lib/observatorySettings'
import {
  clearCacheEndpoint,
  getCacheStatsEndpoint,
} from '@/server/cache.server'
import { V2Page } from '@/v2/components/V2Page'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'

export const Route = createFileRoute('/v2/settings')({
  component: SettingsRoute,
})

type CacheStats = {
  hits: number
  misses: number
  entries: number
  hitRate: number
  entriesByPrefix: Record<string, number>
}

function SettingsRoute() {
  const { settings, defaults, setSettings, resetToDefaults } =
    useObservatorySettings()
  const { settingsSections } = useObservatoryExtensions()
  const [draft, setDraft] = useState<ObservatorySettings>(settings)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const orderedSettingsSections = useMemo(
    () =>
      [...settingsSections].sort((a, b) => {
        const orderA = a.order ?? 0
        const orderB = b.order ?? 0
        if (orderA !== orderB) return orderA - orderB
        return a.title.localeCompare(b.title)
      }),
    [settingsSections],
  )
  const dirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(settings),
    [draft, settings],
  )

  useEffect(() => {
    setDraft(settings)
  }, [settings])

  useEffect(() => {
    void fetchStats()
  }, [])

  async function fetchStats() {
    setStatsLoading(true)
    try {
      setStats(await getCacheStatsEndpoint())
    } catch {
      setStats(null)
    } finally {
      setStatsLoading(false)
    }
  }

  async function clearCache() {
    setStatsLoading(true)
    try {
      await clearCacheEndpoint()
      await fetchStats()
    } catch {
      setStatsLoading(false)
    }
  }

  function save() {
    setError(null)
    const validation = validateSettings(draft)
    if (validation) {
      setError(validation)
      return
    }
    setSettings(draft)
  }

  return (
    <V2Page
      kicker="Settings"
      title="Observatory settings"
      description="Edit operator preferences, extension options, and local maintenance controls."
      action={
        <span className="phlo-v2-pill">
          <Settings className="size-3.5" />
          {dirty ? 'unsaved changes' : 'saved'}
        </span>
      }
    >
      <section className="phlo-v2-settings-workbench">
        <div className="phlo-v2-settings-toolbar">
          <div>
            <strong>Preferences</strong>
            <span>
              Defaults come from the server; overrides are saved for this
              browser and synced where phlo-api exposes a settings contract.
            </span>
          </div>
          <div className="phlo-v2-action-row">
            <button
              onClick={() => {
                resetToDefaults()
                setError(null)
              }}
              type="button"
            >
              <RotateCcw className="size-3.5" />
              Reset
            </button>
            <button disabled={!dirty} onClick={save} type="button">
              <Save className="size-3.5" />
              Save
            </button>
          </div>
        </div>

        {error && <div className="phlo-v2-settings-error">{error}</div>}

        <SettingsPanel
          description="Connection endpoints used by legacy Observatory workflows and detail links."
          icon={<Wifi className="size-4" />}
          title="Connections"
        >
          <SettingField
            hint={`Default: ${defaults.connections.dagsterGraphqlUrl}`}
            label="Dagster GraphQL URL"
          >
            <TextInput
              value={draft.connections.dagsterGraphqlUrl}
              onChange={(value) =>
                setDraft((current) => ({
                  ...current,
                  connections: {
                    ...current.connections,
                    dagsterGraphqlUrl: value,
                  },
                }))
              }
            />
          </SettingField>
          <SettingField
            hint={`Default: ${defaults.connections.trinoUrl}`}
            label="Trino URL"
          >
            <TextInput
              value={draft.connections.trinoUrl}
              onChange={(value) =>
                setDraft((current) => ({
                  ...current,
                  connections: { ...current.connections, trinoUrl: value },
                }))
              }
            />
          </SettingField>
          <SettingField
            hint={`Default: ${defaults.connections.nessieUrl}`}
            label="Nessie URL"
          >
            <TextInput
              value={draft.connections.nessieUrl}
              onChange={(value) =>
                setDraft((current) => ({
                  ...current,
                  connections: { ...current.connections, nessieUrl: value },
                }))
              }
            />
          </SettingField>
        </SettingsPanel>

        <SettingsPanel
          description="Defaults used when opening data and catalog views."
          icon={<SlidersHorizontal className="size-4" />}
          title="Defaults"
        >
          <div className="phlo-v2-settings-columns">
            <SettingField label="Branch">
              <TextInput
                value={draft.defaults.branch}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    defaults: { ...current.defaults, branch: value },
                  }))
                }
              />
            </SettingField>
            <SettingField label="Catalog">
              <TextInput
                value={draft.defaults.catalog}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    defaults: { ...current.defaults, catalog: value },
                  }))
                }
              />
            </SettingField>
            <SettingField label="Schema">
              <TextInput
                value={draft.defaults.schema}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    defaults: { ...current.defaults, schema: value },
                  }))
                }
              />
            </SettingField>
          </div>
        </SettingsPanel>

        <SettingsPanel
          description="SQL execution limits and read-only protections."
          icon={<Database className="size-4" />}
          title="Query"
        >
          <div className="phlo-v2-settings-columns">
            <SettingField label="Default LIMIT">
              <NumberInput
                value={draft.query.defaultLimit}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    query: { ...current.query, defaultLimit: value },
                  }))
                }
              />
            </SettingField>
            <SettingField label="Max LIMIT">
              <NumberInput
                value={draft.query.maxLimit}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    query: { ...current.query, maxLimit: value },
                  }))
                }
              />
            </SettingField>
            <SettingField label="Timeout (ms)">
              <NumberInput
                value={draft.query.timeoutMs}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    query: { ...current.query, timeoutMs: value },
                  }))
                }
              />
            </SettingField>
          </div>
          <ToggleRow
            checked={draft.query.readOnlyMode}
            description="Blocks non-read-only statements and enforces limits in SQL workflows."
            label="Read-only mode"
            onChange={(checked) =>
              setDraft((current) => ({
                ...current,
                query: { ...current.query, readOnlyMode: checked },
              }))
            }
          />
        </SettingsPanel>

        <SettingsPanel
          description="Display preferences shared by v1 and v2."
          icon={<Gauge className="size-4" />}
          title="Interface"
        >
          <div className="phlo-v2-settings-columns">
            <SettingField label="Density">
              <SelectInput
                options={[
                  ['comfortable', 'Comfortable'],
                  ['compact', 'Compact'],
                ]}
                value={draft.ui.density}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    ui: {
                      ...current.ui,
                      density: value as ObservatorySettings['ui']['density'],
                    },
                  }))
                }
              />
            </SettingField>
            <SettingField label="Date format">
              <SelectInput
                options={[
                  ['iso', 'ISO'],
                  ['local', 'Local'],
                ]}
                value={draft.ui.dateFormat}
                onChange={(value) =>
                  setDraft((current) => ({
                    ...current,
                    ui: {
                      ...current.ui,
                      dateFormat:
                        value as ObservatorySettings['ui']['dateFormat'],
                    },
                  }))
                }
              />
            </SettingField>
          </div>
        </SettingsPanel>

        <SettingsPanel
          description="Authentication and live update behavior."
          icon={<KeyRound className="size-4" />}
          title="Access and updates"
        >
          <SettingField
            hint="Used when OBSERVATORY_AUTH_ENABLED=true."
            label="Auth token"
          >
            <TextInput
              placeholder="Enter auth token..."
              type="password"
              value={draft.auth?.token ?? ''}
              onChange={(value) =>
                setDraft((current) => ({
                  ...current,
                  auth: { ...current.auth, token: value || undefined },
                }))
              }
            />
          </SettingField>
          <ToggleRow
            checked={draft.realtime?.enabled ?? true}
            description="Automatically poll dashboard and quality views for updates."
            label="Enable auto-refresh"
            onChange={(checked) =>
              setDraft((current) => ({
                ...current,
                realtime: {
                  enabled: checked,
                  intervalMs: current.realtime?.intervalMs ?? 5000,
                },
              }))
            }
          />
          <SettingField label="Polling interval (ms)">
            <NumberInput
              disabled={!(draft.realtime?.enabled ?? true)}
              max={60000}
              min={1000}
              step={1000}
              value={draft.realtime?.intervalMs ?? 5000}
              onChange={(value) =>
                setDraft((current) => ({
                  ...current,
                  realtime: {
                    enabled: current.realtime?.enabled ?? true,
                    intervalMs: value,
                  },
                }))
              }
            />
          </SettingField>
        </SettingsPanel>

        {orderedSettingsSections.map((section) => {
          const SectionComponent = section.component
          return (
            <SettingsPanel
              description={
                section.description ??
                'Extension-provided settings registered with Observatory.'
              }
              icon={<Settings className="size-4" />}
              key={section.id}
              title={section.title}
            >
              <SectionComponent />
            </SettingsPanel>
          )
        })}

        <SettingsPanel
          description="Metadata cache visibility and maintenance."
          icon={<RefreshCw className="size-4" />}
          title="Advanced"
        >
          <div className="phlo-v2-cache-header">
            <strong>Metadata cache</strong>
            <div className="phlo-v2-action-row">
              <button
                disabled={statsLoading}
                onClick={() => void fetchStats()}
                type="button"
              >
                <RefreshCw className="size-3.5" />
                Refresh
              </button>
              <button
                disabled={statsLoading}
                onClick={() => void clearCache()}
                type="button"
              >
                Clear cache
              </button>
            </div>
          </div>
          <div className="phlo-v2-cache-grid">
            <CacheMetric label="Hits" value={stats?.hits ?? 0} />
            <CacheMetric label="Misses" value={stats?.misses ?? 0} />
            <CacheMetric
              label="Hit rate"
              value={`${(((stats?.hitRate ?? 0) as number) * 100).toFixed(1)}%`}
            />
            <CacheMetric label="Entries" value={stats?.entries ?? 0} />
          </div>
          {stats?.entriesByPrefix &&
            Object.keys(stats.entriesByPrefix).length > 0 && (
              <div className="phlo-v2-detail-list">
                {Object.entries(stats.entriesByPrefix).map(
                  ([prefix, count]) => (
                    <div className="phlo-v2-mini-row" key={prefix}>
                      <span>{prefix}</span>
                      <small>{count}</small>
                    </div>
                  ),
                )}
              </div>
            )}
        </SettingsPanel>
      </section>
    </V2Page>
  )
}

function SettingsPanel({
  children,
  description,
  icon,
  title,
}: {
  children: ReactNode
  description: string
  icon: ReactNode
  title: string
}) {
  return (
    <section className="phlo-v2-settings-panel">
      <div className="phlo-v2-callout-title">
        {icon}
        {title}
      </div>
      <p>{description}</p>
      <div className="phlo-v2-settings-panel-body">{children}</div>
    </section>
  )
}

function SettingField({
  children,
  hint,
  label,
}: {
  children: ReactNode
  hint?: string
  label: string
}) {
  return (
    <label className="phlo-v2-settings-field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  )
}

function TextInput({
  onChange,
  type = 'text',
  ...props
}: {
  disabled?: boolean
  onChange: (value: string) => void
  placeholder?: string
  type?: string
  value: string
}) {
  return (
    <input
      {...props}
      type={type}
      onChange={(event) => onChange(event.target.value)}
    />
  )
}

function NumberInput({
  disabled,
  max,
  min,
  onChange,
  step,
  value,
}: {
  disabled?: boolean
  max?: number
  min?: number
  onChange: (value: number) => void
  step?: number
  value: number
}) {
  return (
    <input
      disabled={disabled}
      max={max}
      min={min}
      step={step}
      type="number"
      value={value}
      onChange={(event) => onChange(Number(event.target.value) || 0)}
    />
  )
}

function SelectInput({
  onChange,
  options,
  value,
}: {
  onChange: (value: string) => void
  options: Array<[string, string]>
  value: string
}) {
  return (
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      {options.map(([optionValue, label]) => (
        <option key={optionValue} value={optionValue}>
          {label}
        </option>
      ))}
    </select>
  )
}

function ToggleRow({
  checked,
  description,
  label,
  onChange,
}: {
  checked: boolean
  description: string
  label: string
  onChange: (checked: boolean) => void
}) {
  return (
    <label className="phlo-v2-toggle-row">
      <input
        checked={checked}
        type="checkbox"
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>
        <strong>{label}</strong>
        <small>{description}</small>
      </span>
    </label>
  )
}

function CacheMetric({
  label,
  value,
}: {
  label: string
  value: number | string
}) {
  return (
    <div className="phlo-v2-cache-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function validateSettings(settings: ObservatorySettings): string | null {
  if (!settings.connections.dagsterGraphqlUrl.trim()) {
    return 'Dagster GraphQL URL is required.'
  }
  if (!settings.connections.trinoUrl.trim()) return 'Trino URL is required.'
  if (!settings.connections.nessieUrl.trim()) return 'Nessie URL is required.'
  if (settings.query.defaultLimit > settings.query.maxLimit) {
    return 'Default LIMIT must be less than or equal to Max LIMIT.'
  }
  return null
}

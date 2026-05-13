import { createFileRoute } from '@tanstack/react-router'
import {
  Database,
  Gauge,
  KeyRound,
  Plug,
  RefreshCw,
  RotateCcw,
  Save,
  Settings,
  SlidersHorizontal,
} from 'lucide-react'
import { useEffect, useId, useMemo, useReducer } from 'react'
import type { Dispatch, ReactNode } from 'react'

import type { ObservatorySettings } from '@/lib/observatorySettings'
import type { V2Capabilities, V2ResourceResult } from '@/v2/api/types'
import { useObservatoryExtensions } from '@/extensions/registry'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import {
  clearCacheEndpoint,
  getCacheStatsEndpoint,
} from '@/server/cache.server'
import { getV2Capabilities } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { loadCachedResource } from '@/v2/routes/liveResource'

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

type SettingsRouteState = {
  capabilities: V2ResourceResult<V2Capabilities> | null
  draft: ObservatorySettings
  error: string | null
  stats: CacheStats | null
  statsLoading: boolean
}

type SettingsRouteAction =
  | { type: 'draft'; draft: ObservatorySettings }
  | {
      type: 'updateDraft'
      update: (draft: ObservatorySettings) => ObservatorySettings
    }
  | { type: 'error'; error: string | null }
  | { type: 'statsLoading'; loading: boolean }
  | { type: 'stats'; stats: CacheStats | null }
  | {
      type: 'capabilities'
      capabilities: V2ResourceResult<V2Capabilities> | null
    }

function settingsRouteReducer(
  state: SettingsRouteState,
  action: SettingsRouteAction,
): SettingsRouteState {
  switch (action.type) {
    case 'draft':
      return { ...state, draft: action.draft }
    case 'updateDraft':
      return { ...state, draft: action.update(state.draft) }
    case 'error':
      return { ...state, error: action.error }
    case 'statsLoading':
      return { ...state, statsLoading: action.loading }
    case 'stats':
      return { ...state, stats: action.stats, statsLoading: false }
    case 'capabilities':
      return { ...state, capabilities: action.capabilities }
  }
}

function updateDraft(
  dispatch: Dispatch<SettingsRouteAction>,
  update: (draft: ObservatorySettings) => ObservatorySettings,
) {
  dispatch({ type: 'updateDraft', update })
}

export function SettingsRoute() {
  return useSettingsRoute()
}

function useSettingsRoute() {
  const { settings, setSettings, resetToDefaults } = useObservatorySettings()
  const { settingsSections } = useObservatoryExtensions()
  const [{ capabilities, draft, error, stats, statsLoading }, dispatch] =
    useReducer(settingsRouteReducer, {
      capabilities: null,
      draft: settings,
      error: null,
      stats: null,
      statsLoading: false,
    })
  const orderedSettingsSections = useMemo(
    () =>
      settingsSections.slice().sort((a, b) => {
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
  const capabilityFeatures = capabilities?.data?.features ?? {}

  useEffect(() => {
    dispatch({ type: 'draft', draft: settings })
  }, [settings])

  useEffect(() => {
    void fetchStats()
    void loadCachedResource('v2:capabilities', getV2Capabilities, {
      staleMs: 120_000,
    }).then((nextCapabilities) =>
      dispatch({ type: 'capabilities', capabilities: nextCapabilities }),
    )
  }, [])

  async function fetchStats() {
    dispatch({ type: 'statsLoading', loading: true })
    try {
      dispatch({ type: 'stats', stats: await getCacheStatsEndpoint() })
    } catch {
      dispatch({ type: 'stats', stats: null })
    } finally {
      dispatch({ type: 'statsLoading', loading: false })
    }
  }

  async function clearCache() {
    dispatch({ type: 'statsLoading', loading: true })
    try {
      await clearCacheEndpoint()
      await fetchStats()
    } catch {
      dispatch({ type: 'statsLoading', loading: false })
    }
  }

  function save() {
    dispatch({ type: 'error', error: null })
    const validation = validateSettings(draft)
    if (validation) {
      dispatch({ type: 'error', error: validation })
      return
    }
    setSettings(draft)
  }

  return (
    <V2Page
      kicker="Settings"
      title="Observatory settings"
      description="Edit browser preferences, inspect capabilities, and run local maintenance controls."
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
              Preferences are saved for this browser. Project and provider
              settings appear when phlo-api exposes a write contract.
            </span>
          </div>
          <div className="phlo-v2-action-row">
            <button
              onClick={() => {
                resetToDefaults()
                dispatch({ type: 'error', error: null })
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
          description="Defaults used when opening data and catalog views."
          icon={<SlidersHorizontal className="size-4" />}
          title="Defaults"
        >
          <div className="phlo-v2-settings-columns">
            {capabilityFeatures.branches && (
              <SettingField label="Branch">
                <TextInput
                  value={draft.defaults.branch}
                  onChange={(value) =>
                    updateDraft(dispatch, (current) => ({
                      ...current,
                      defaults: { ...current.defaults, branch: value },
                    }))
                  }
                />
              </SettingField>
            )}
            <SettingField label="Catalog">
              <TextInput
                value={draft.defaults.catalog}
                onChange={(value) =>
                  updateDraft(dispatch, (current) => ({
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
                  updateDraft(dispatch, (current) => ({
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
                  updateDraft(dispatch, (current) => ({
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
                  updateDraft(dispatch, (current) => ({
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
                  updateDraft(dispatch, (current) => ({
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
              updateDraft(dispatch, (current) => ({
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
                  updateDraft(dispatch, (current) => ({
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
                  updateDraft(dispatch, (current) => ({
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
          description="Authentication token and live update behavior for this browser session."
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
                updateDraft(dispatch, (current) => ({
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
              updateDraft(dispatch, (current) => ({
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
                updateDraft(dispatch, (current) => ({
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
          description="Installed providers decide which Observatory surfaces appear in navigation."
          icon={<Plug className="size-4" />}
          title="Capabilities"
        >
          <div className="phlo-v2-detail-list">
            {(capabilities?.data?.pages ?? []).map((page) => (
              <div className="phlo-v2-mini-row" key={page.id}>
                <span>{page.label}</span>
                <small>
                  {page.available
                    ? page.providers.length
                      ? page.providers.join(', ')
                      : 'core'
                    : (page.reason ?? 'No provider installed')}
                </small>
              </div>
            ))}
            {capabilities?.error && (
              <div className="phlo-v2-mini-row">
                <span>Capability discovery</span>
                <small>{capabilities.error}</small>
              </div>
            )}
          </div>
        </SettingsPanel>

        <SettingsPanel
          description="Operator maintenance for Observatory read-model caches."
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
              value={`${((stats?.hitRate ?? 0) * 100).toFixed(1)}%`}
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
  const inputId = useId()
  return (
    <label className="phlo-v2-toggle-row" htmlFor={inputId}>
      <input
        id={inputId}
        aria-label={label}
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
  if (settings.query.defaultLimit > settings.query.maxLimit) {
    return 'Default LIMIT must be less than or equal to Max LIMIT.'
  }
  return null
}

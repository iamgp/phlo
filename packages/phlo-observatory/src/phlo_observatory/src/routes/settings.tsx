import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'

import type { ObservatorySettings } from '@/lib/observatorySettings'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import {
  clearCacheEndpoint,
  getCacheStatsEndpoint,
} from '@/server/cache.server'

export const Route = createFileRoute('/settings')({
  component: SettingsPage,
})

type CacheStats = {
  hits: number
  misses: number
  entries: number
  hitRate: number
  entriesByPrefix: Record<string, number>
}

function SettingsPage() {
  const { settings, defaults, setSettings, resetToDefaults } =
    useObservatorySettings()
  const [draft, setDraft] = useState<ObservatorySettings>(settings)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const isDirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(settings),
    [draft, settings],
  )

  useEffect(() => {
    setDraft(settings)
  }, [settings])

  const fetchStats = async () => {
    setStatsLoading(true)
    try {
      const data = await getCacheStatsEndpoint()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch cache stats:', err)
    } finally {
      setStatsLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const handleClearCache = async () => {
    setStatsLoading(true)
    try {
      await clearCacheEndpoint()
      await fetchStats()
    } catch (err) {
      console.error('Failed to clear cache:', err)
      setStatsLoading(false)
    }
  }

  const save = () => {
    setError(null)

    if (!draft.connections.dagsterGraphqlUrl.trim()) {
      setError('Dagster GraphQL URL is required.')
      return
    }
    if (!draft.connections.trinoUrl.trim()) {
      setError('Trino URL is required.')
      return
    }
    if (!draft.connections.nessieUrl.trim()) {
      setError('Nessie URL is required.')
      return
    }
    if (draft.query.defaultLimit > draft.query.maxLimit) {
      setError('Default LIMIT must be <= Max LIMIT.')
      return
    }

    setSettings(draft)
  }

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-3xl px-4 py-6 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">
              Overrides are stored in your browser. Defaults come from the
              server environment.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => resetToDefaults()}>
              Reset to defaults
            </Button>
            <Button onClick={save} disabled={!isDirty}>
              Save
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Connections</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field
              label="Dagster GraphQL URL"
              hint={`Default: ${defaults.connections.dagsterGraphqlUrl}`}
            >
              <Input
                value={draft.connections.dagsterGraphqlUrl}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    connections: {
                      ...prev.connections,
                      dagsterGraphqlUrl: e.target.value,
                    },
                  }))
                }
              />
            </Field>
            <Field
              label="Trino URL"
              hint={`Default: ${defaults.connections.trinoUrl}`}
            >
              <Input
                value={draft.connections.trinoUrl}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    connections: {
                      ...prev.connections,
                      trinoUrl: e.target.value,
                    },
                  }))
                }
              />
            </Field>
            <Field
              label="Nessie URL"
              hint={`Default: ${defaults.connections.nessieUrl}`}
            >
              <Input
                value={draft.connections.nessieUrl}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    connections: {
                      ...prev.connections,
                      nessieUrl: e.target.value,
                    },
                  }))
                }
              />
            </Field>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Defaults</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <Field label="Branch">
              <Input
                value={draft.defaults.branch}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    defaults: { ...prev.defaults, branch: e.target.value },
                  }))
                }
              />
            </Field>
            <Field label="Catalog">
              <Input
                value={draft.defaults.catalog}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    defaults: { ...prev.defaults, catalog: e.target.value },
                  }))
                }
              />
            </Field>
            <Field label="Schema">
              <Input
                value={draft.defaults.schema}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    defaults: { ...prev.defaults, schema: e.target.value },
                  }))
                }
              />
            </Field>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Query</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Default LIMIT">
                <Input
                  type="number"
                  value={draft.query.defaultLimit}
                  onChange={(e) =>
                    setDraft((prev) => ({
                      ...prev,
                      query: {
                        ...prev.query,
                        defaultLimit: Number(e.target.value) || 0,
                      },
                    }))
                  }
                />
              </Field>
              <Field label="Max LIMIT">
                <Input
                  type="number"
                  value={draft.query.maxLimit}
                  onChange={(e) =>
                    setDraft((prev) => ({
                      ...prev,
                      query: {
                        ...prev.query,
                        maxLimit: Number(e.target.value) || 0,
                      },
                    }))
                  }
                />
              </Field>
              <Field label="Timeout (ms)">
                <Input
                  type="number"
                  value={draft.query.timeoutMs}
                  onChange={(e) =>
                    setDraft((prev) => ({
                      ...prev,
                      query: {
                        ...prev.query,
                        timeoutMs: Number(e.target.value) || 0,
                      },
                    }))
                  }
                />
              </Field>
            </div>

            <Separator />

            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 accent-primary"
                checked={draft.query.readOnlyMode}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    query: { ...prev.query, readOnlyMode: e.target.checked },
                  }))
                }
              />
              <div>
                <div className="text-sm font-medium">
                  Read-only mode (recommended)
                </div>
                <div className="text-xs text-muted-foreground">
                  When enabled, the SQL runner blocks non-read-only statements
                  and enforces limits.
                </div>
              </div>
            </label>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>UI</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="Density">
              <select
                value={draft.ui.density}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    ui: {
                      ...prev.ui,
                      density: e.target.value as 'comfortable' | 'compact',
                    },
                  }))
                }
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="comfortable">Comfortable</option>
                <option value="compact">Compact</option>
              </select>
            </Field>
            <Field label="Date format">
              <select
                value={draft.ui.dateFormat}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    ui: {
                      ...prev.ui,
                      dateFormat: e.target.value as 'iso' | 'local',
                    },
                  }))
                }
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="iso">ISO (2025-12-16)</option>
                <option value="local">Local</option>
              </select>
            </Field>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Authentication</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field
              label="Auth Token"
              hint="Token for authenticating with Observatory when OBSERVATORY_AUTH_ENABLED=true"
            >
              <Input
                type="password"
                placeholder="Enter auth token..."
                value={draft.auth?.token ?? ''}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    auth: { ...prev.auth, token: e.target.value || undefined },
                  }))
                }
              />
            </Field>
            <div className="text-xs text-muted-foreground">
              When auth is enabled on the server, provide the token here to
              access Observatory.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Real-time Updates</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 accent-primary"
                checked={draft.realtime?.enabled ?? true}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    realtime: {
                      enabled: e.target.checked,
                      intervalMs: prev.realtime?.intervalMs ?? 5000,
                    },
                  }))
                }
              />
              <div>
                <div className="text-sm font-medium">Enable auto-refresh</div>
                <div className="text-xs text-muted-foreground">
                  Automatically poll for updates on dashboard and quality pages.
                </div>
              </div>
            </label>

            <Field label="Polling Interval (ms)">
              <Input
                type="number"
                min={1000}
                max={60000}
                step={1000}
                value={draft.realtime?.intervalMs ?? 5000}
                disabled={!(draft.realtime?.enabled ?? true)}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    realtime: {
                      enabled: prev.realtime?.enabled ?? true,
                      intervalMs: Number(e.target.value) || 5000,
                    },
                  }))
                }
              />
            </Field>
            <div className="text-xs text-muted-foreground">
              How often to check for updates (1000ms - 60000ms). Lower values
              mean more requests.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Advanced</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Metadata Cache Stats</div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchStats}
                  disabled={statsLoading}
                >
                  Refresh
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleClearCache}
                  disabled={statsLoading}
                >
                  Clear Cache
                </Button>
              </div>
            </div>

            {stats && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">Hits</div>
                  <div className="text-2xl font-bold">{stats.hits}</div>
                </div>
                <div className="rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">Misses</div>
                  <div className="text-2xl font-bold">{stats.misses}</div>
                </div>
                <div className="rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">Hit Rate</div>
                  <div className="text-2xl font-bold">
                    {(stats.hitRate * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">Entries</div>
                  <div className="text-2xl font-bold">{stats.entries}</div>
                </div>
              </div>
            )}

            {stats?.entriesByPrefix &&
              Object.keys(stats.entriesByPrefix).length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-medium">Entries by Prefix</div>
                  <div className="rounded-md border bg-muted/50 p-2 text-xs font-mono">
                    {Object.entries(stats.entriesByPrefix).map(
                      ([prefix, count]) => (
                        <div key={prefix} className="flex justify-between">
                          <span>{prefix}</span>
                          <span>{count}</span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      {children}
      {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
    </div>
  )
}

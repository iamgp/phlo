import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'

import type { ObservatorySettings } from '@/lib/observatorySettings'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

export const Route = createFileRoute('/settings')({
  component: SettingsPage,
})

function SettingsPage() {
  const { settings, defaults, setSettings, resetToDefaults } =
    useObservatorySettings()
  const [draft, setDraft] = useState<ObservatorySettings>(settings)
  const [error, setError] = useState<string | null>(null)
  const isDirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(settings),
    [draft, settings],
  )

  useEffect(() => {
    setDraft(settings)
  }, [settings])

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

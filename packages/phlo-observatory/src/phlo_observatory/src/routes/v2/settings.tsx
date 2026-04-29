import { createFileRoute } from '@tanstack/react-router'
import { RotateCcw, Save, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'

import type { V2ResourceResult, V2Settings } from '@/v2/api/types'
import { getV2Settings } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'

export const Route = createFileRoute('/v2/settings')({
  component: SettingsRoute,
})

function SettingsRoute() {
  const [result, setResult] = useState<V2ResourceResult<V2Settings>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getV2Settings().then(setResult)
  }, [])

  const settings = result.data?.items ?? []

  return (
    <V2Page
      kicker="Settings"
      title="Control-plane preferences"
      description="Manage Observatory behavior without provider implementation URLs."
      action={
        <span className="phlo-v2-pill">
          <Settings className="size-3.5" />
          {settings.length} settings
        </span>
      }
    >
      <div className="phlo-v2-settings-surface">
        <div className="phlo-v2-browser-toolbar">
          <span>
            <Settings className="size-4" />
            Preferences
          </span>
          <span className="phlo-v2-pill">operator safe</span>
        </div>
        <div className="phlo-v2-list">
          {settings.map((setting) => (
            <label className="phlo-v2-setting-row" key={setting.id}>
              <div className="phlo-v2-row-main">
                <div className="phlo-v2-row-title">{setting.label}</div>
                <div className="phlo-v2-row-meta">
                  {setting.description ?? setting.kind}
                </div>
              </div>
              <input
                readOnly
                value={setting.value === null ? 'unset' : String(setting.value)}
              />
            </label>
          ))}
          {settings.length === 0 && (
            <div className="phlo-v2-row">
              <div className="phlo-v2-row-main">
                <div className="phlo-v2-row-title">
                  No preferences returned yet
                </div>
                <div className="phlo-v2-row-meta">
                  Operator-safe settings will appear here.
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="phlo-v2-action-row phlo-v2-settings-actions">
          <button
            disabled
            title="Saving settings requires a safe write contract."
            type="button"
          >
            <Save className="size-3.5" />
            Save
          </button>
          <button
            disabled
            title="Resetting settings requires a safe write contract."
            type="button"
          >
            <RotateCcw className="size-3.5" />
            Reset
          </button>
        </div>
        {result.error && (
          <div className="phlo-v2-panel-footer">{result.error}</div>
        )}
      </div>
    </V2Page>
  )
}

import { createFileRoute } from '@tanstack/react-router'
import { Plug, Route as RouteIcon, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'

import type {
  V2Extension,
  V2ExtensionDetail,
  V2ResourceResult,
} from '@/v2/api/types'
import { getV2ExtensionDetail, getV2Extensions } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/extensions')({
  component: Extensions,
})

export function Extensions() {
  const result = useLiveResource(getV2Extensions)
  const extensions = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    extensions.find((extension) => extension.id === selectedId) ?? extensions[0]
  const [detail, setDetail] = useState<V2ResourceResult<V2ExtensionDetail>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getV2ExtensionDetail({ data: { extensionId: selected.id } }).then(
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
      kicker="Extensions"
      title="Capability registry"
      description="Routes, navigation, and settings scopes exposed by installed Observatory extensions."
      action={
        <span className="phlo-v2-pill">{extensions.length} installed</span>
      }
    >
      <section className="phlo-v2-extension-grid">
        {extensions.map((extension) => (
          <button
            className="phlo-v2-extension-row phlo-v2-select-row"
            data-active={extension.id === selected?.id}
            key={extension.id}
            onClick={() => setSelectedId(extension.id)}
            type="button"
          >
            <Plug className="size-4" />
            <div>
              <h2>{extension.name}</h2>
              <p>{extensionSummary(extension) || 'Extension manifest'}</p>
            </div>
            <span className="phlo-v2-pill">
              {extension.enabled ? 'enabled' : 'disabled'}
            </span>
          </button>
        ))}
      </section>
      <section className="phlo-v2-surface-grid">
        <div className="phlo-v2-callout">
          <div className="phlo-v2-callout-title">
            <RouteIcon className="size-4" />
            Routes and navigation
          </div>
          <div className="phlo-v2-detail-list">
            {detail.data?.routes.map((route) => (
              <div className="phlo-v2-mini-row" key={route}>
                <span>{route}</span>
                <small>manifest route</small>
              </div>
            ))}
            {detail.data && detail.data.routes.length === 0 && (
              <p>No routes registered for this extension.</p>
            )}
            {detail.data?.nav.map((navItem) => (
              <div className="phlo-v2-mini-row" key={navItem}>
                <span>{navItem}</span>
                <small>navigation item</small>
              </div>
            ))}
          </div>
        </div>
        <div className="phlo-v2-callout">
          <div className="phlo-v2-callout-title">
            <Settings className="size-4" />
            Settings scopes
          </div>
          <div className="phlo-v2-detail-list">
            <div className="phlo-v2-mini-row">
              <span>{selected?.name ?? 'No extension selected'}</span>
              <small>
                {detail.data?.extension.settings_scope ?? 'no scope'}
              </small>
            </div>
            {detail.data?.capabilities.map((capability) => (
              <div className="phlo-v2-mini-row" key={capability.id}>
                <span>{capability.label}</span>
                <small>{capability.kind}</small>
              </div>
            ))}
            {detail.data && detail.data.capabilities.length === 0 && (
              <p>No extension capabilities returned yet.</p>
            )}
          </div>
        </div>
      </section>
      {detail.error && (
        <div className="phlo-v2-panel-footer">{detail.error}</div>
      )}
      {result.error && (
        <div className="phlo-v2-panel-footer">{result.error}</div>
      )}
    </V2Page>
  )
}

function extensionSummary(extension: V2Extension): string {
  return [
    extension.version ? `v${extension.version}` : null,
    extension.routes.length ? `${extension.routes.length} routes` : null,
    extension.nav.length ? `${extension.nav.length} nav items` : null,
    extension.settings_scope,
  ]
    .filter(Boolean)
    .join(' · ')
}

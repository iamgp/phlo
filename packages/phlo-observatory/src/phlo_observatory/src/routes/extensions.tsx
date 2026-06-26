import { createFileRoute } from '@tanstack/react-router'
import { Plug, Route as RouteIcon, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'

import type {
  ObservatoryExtension,
  ObservatoryExtensionDetail,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import {
  getObservatoryExtensionDetail,
  getObservatoryExtensions,
} from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/extensions')({
  component: Extensions,
})

export function Extensions() {
  const result = useLiveResource(getObservatoryExtensions)
  const extensions = result.data ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    extensions.find((extension) => extension.id === selectedId) ?? extensions[0]
  const [detail, setDetail] = useState<
    ObservatoryResourceResult<ObservatoryExtensionDetail>
  >({
    data: null,
    error: null,
  })

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    void getObservatoryExtensionDetail({
      data: { extensionId: selected.id },
    }).then((next) => {
      if (!cancelled) setDetail(next)
    })
    return () => {
      cancelled = true
    }
  }, [selected])

  return (
    <ObservatoryPage
      kicker="Extensions"
      title="Capability registry"
      description="Routes, navigation, and settings scopes exposed by installed Observatory extensions."
      action={
        <span className="phlo-observatory-pill">
          {extensions.length} installed
        </span>
      }
    >
      <section className="phlo-observatory-extension-grid">
        {extensions.map((extension) => (
          <button
            className="phlo-observatory-extension-row phlo-observatory-select-row"
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
            <span className="phlo-observatory-pill">
              {extension.enabled ? 'enabled' : 'disabled'}
            </span>
          </button>
        ))}
      </section>
      <section className="phlo-observatory-surface-grid">
        <div className="phlo-observatory-callout">
          <div className="phlo-observatory-callout-title">
            <RouteIcon className="size-4" />
            Routes and navigation
          </div>
          <div className="phlo-observatory-detail-list">
            {detail.data?.routes.map((route) => (
              <div className="phlo-observatory-mini-row" key={route}>
                <span>{route}</span>
                <small>manifest route</small>
              </div>
            ))}
            {detail.data && detail.data.routes.length === 0 && (
              <p>No routes registered for this extension.</p>
            )}
            {detail.data?.nav.map((navItem) => (
              <div className="phlo-observatory-mini-row" key={navItem}>
                <span>{navItem}</span>
                <small>navigation item</small>
              </div>
            ))}
          </div>
        </div>
        <div className="phlo-observatory-callout">
          <div className="phlo-observatory-callout-title">
            <Settings className="size-4" />
            Settings scopes
          </div>
          <div className="phlo-observatory-detail-list">
            <div className="phlo-observatory-mini-row">
              <span>{selected?.name ?? 'No extension selected'}</span>
              <small>
                {detail.data?.extension.settings_scope ?? 'no scope'}
              </small>
            </div>
            {detail.data?.capabilities.map((capability) => (
              <div className="phlo-observatory-mini-row" key={capability.id}>
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
        <div className="phlo-observatory-panel-footer">{detail.error}</div>
      )}
      {result.error && (
        <div className="phlo-observatory-panel-footer">{result.error}</div>
      )}
    </ObservatoryPage>
  )
}

function extensionSummary(extension: ObservatoryExtension): string {
  return [
    extension.version ? `v${extension.version}` : null,
    extension.routes.length ? `${extension.routes.length} routes` : null,
    extension.nav.length ? `${extension.nav.length} nav items` : null,
    extension.settings_scope,
  ]
    .filter(Boolean)
    .join(' · ')
}

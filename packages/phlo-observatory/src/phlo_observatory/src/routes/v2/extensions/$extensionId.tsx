import { createFileRoute } from '@tanstack/react-router'
import { Navigation, Plug, Route as RouteIcon, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type { V2ExtensionDetail, V2ResourceResult } from '@/v2/api/types'
import { getV2ExtensionDetail } from '@/v2/api/resources'
import { V2Page } from '@/v2/components/V2Page'

export const Route = createFileRoute('/v2/extensions/$extensionId')({
  component: ExtensionDetailRoute,
})

function ExtensionDetailRoute() {
  const { extensionId } = Route.useParams()
  return <ExtensionDetailView extensionId={extensionId} />
}

export function ExtensionDetailView({ extensionId }: { extensionId: string }) {
  const [result, setResult] = useState<V2ResourceResult<V2ExtensionDetail>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getV2ExtensionDetail({ data: { extensionId } })
      .then(setResult)
      .catch(() =>
        setResult({
          data: null,
          error: 'Extension detail is unavailable.',
        }),
      )
  }, [extensionId])

  const detail = result.data
  const extension = detail?.extension

  return (
    <V2Page
      action={
        <span className="phlo-v2-pill">
          {extension?.enabled ? 'enabled' : 'disabled'}
        </span>
      }
      description="Extension manifest, routes, and settings scope."
      kicker="Extension"
      title={extension?.name ?? extensionId}
    >
      {detail && extension ? (
        <section className="phlo-v2-surface-grid">
          <div className="phlo-v2-list-surface">
            <div className="phlo-v2-browser-toolbar">
              <span>
                <RouteIcon className="size-4" />
                Routes
              </span>
              <span className="phlo-v2-pill">
                {detail.routes.length} routes
              </span>
            </div>
            <div className="phlo-v2-detail-list phlo-v2-detail-list-padded">
              {detail.routes.map((route) => (
                <div className="phlo-v2-mini-row" key={route}>
                  <span>{route}</span>
                  <small>route</small>
                </div>
              ))}
              {detail.routes.length === 0 && <p>No routes registered.</p>}
            </div>
          </div>
          <aside className="phlo-v2-inspector">
            <div className="phlo-v2-inspector-label">Manifest</div>
            <h2>{extension.name}</h2>
            <p>{extension.version ?? 'No version returned.'}</p>
            <div className="phlo-v2-detail-list">
              <Mini
                icon={<Plug className="size-3.5" />}
                label="Plugin"
                value={extension.id}
              />
              <Mini
                icon={<Settings className="size-3.5" />}
                label="Settings scope"
                value={extension.settings_scope ?? 'none'}
              />
              <Mini
                icon={<Navigation className="size-3.5" />}
                label="Nav items"
                value={String(detail.nav.length)}
              />
            </div>
          </aside>
        </section>
      ) : (
        <div className="phlo-v2-empty-state">
          {result.error ?? 'Loading extension detail…'}
        </div>
      )}
    </V2Page>
  )
}

function Mini({
  icon,
  label,
  value,
}: {
  icon?: ReactNode
  label: string
  value: string
}) {
  return (
    <div className="phlo-v2-mini-row">
      <span>
        {icon}
        {label}
      </span>
      <small>{value}</small>
    </div>
  )
}

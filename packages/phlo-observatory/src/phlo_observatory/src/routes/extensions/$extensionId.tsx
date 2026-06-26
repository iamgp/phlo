import { createFileRoute } from '@tanstack/react-router'
import { Navigation, Plug, Route as RouteIcon, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryExtensionDetail,
  ObservatoryResourceResult,
} from '@/observatory/api/types'
import { getObservatoryExtensionDetail } from '@/observatory/api/resources'
import { ObservatoryPage } from '@/observatory/components/ObservatoryPage'

export const Route = createFileRoute('/extensions/$extensionId')({
  component: ExtensionDetailRoute,
})

function ExtensionDetailRoute() {
  const { extensionId } = Route.useParams()
  return <ExtensionDetailView extensionId={extensionId} />
}

export function ExtensionDetailView({ extensionId }: { extensionId: string }) {
  const [result, setResult] = useState<
    ObservatoryResourceResult<ObservatoryExtensionDetail>
  >({
    data: null,
    error: null,
  })

  useEffect(() => {
    void getObservatoryExtensionDetail({ data: { extensionId } })
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
    <ObservatoryPage
      action={
        <span className="phlo-observatory-pill">
          {extension?.enabled ? 'enabled' : 'disabled'}
        </span>
      }
      description="Extension manifest, routes, and settings scope."
      kicker="Extension"
      title={extension?.name ?? extensionId}
    >
      {detail && extension ? (
        <section className="phlo-observatory-surface-grid">
          <div className="phlo-observatory-list-surface">
            <div className="phlo-observatory-browser-toolbar">
              <span>
                <RouteIcon className="size-4" />
                Routes
              </span>
              <span className="phlo-observatory-pill">
                {detail.routes.length} routes
              </span>
            </div>
            <div className="phlo-observatory-detail-list phlo-observatory-detail-list-padded">
              {detail.routes.map((route) => (
                <div className="phlo-observatory-mini-row" key={route}>
                  <span>{route}</span>
                  <small>route</small>
                </div>
              ))}
              {detail.routes.length === 0 && <p>No routes registered.</p>}
            </div>
          </div>
          <aside className="phlo-observatory-inspector">
            <div className="phlo-observatory-inspector-label">Manifest</div>
            <h2>{extension.name}</h2>
            <p>{extension.version ?? 'No version returned.'}</p>
            <div className="phlo-observatory-detail-list">
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
        <div className="phlo-observatory-empty-state">
          {result.error ?? 'Loading extension detail…'}
        </div>
      )}
    </ObservatoryPage>
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
    <div className="phlo-observatory-mini-row">
      <span>
        {icon}
        {label}
      </span>
      <small>{value}</small>
    </div>
  )
}

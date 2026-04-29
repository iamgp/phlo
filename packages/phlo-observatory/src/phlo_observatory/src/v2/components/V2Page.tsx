import { AlertCircle } from 'lucide-react'
import type { ReactNode } from 'react'

import type { V2ResourceItem, V2ResourceResult } from '@/v2/api/types'

export function V2Page({
  kicker,
  title,
  description,
  action,
  children,
}: {
  kicker: string
  title: string
  description: string
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <div className="phlo-v2-content">
      <header className="phlo-v2-section-header">
        <div>
          <div className="phlo-v2-kicker">{kicker}</div>
          <h1 className="phlo-v2-title">{title}</h1>
          <p className="phlo-v2-subtitle">{description}</p>
        </div>
        {action}
      </header>
      {children}
    </div>
  )
}

export function V2ResourcePanel({
  title,
  label,
  result,
  emptyTitle = 'No resources registered',
  emptyBody = 'phlo-api v2 has no entries for this surface.',
}: {
  title: string
  label: string
  result: V2ResourceResult<Array<V2ResourceItem>>
  emptyTitle?: string
  emptyBody?: string
}) {
  const rows = result.data ?? []

  return (
    <div className="phlo-v2-panel">
      <div className="phlo-v2-panel-header">
        <h2 className="phlo-v2-panel-title">{title}</h2>
        <span className="phlo-v2-pill">
          {rows.length} {label}
        </span>
      </div>
      <div className="phlo-v2-list">
        {rows.length > 0 ? (
          rows.map((item) => <V2ResourceRow key={item.id} item={item} />)
        ) : (
          <div className="phlo-v2-row">
            <div className="phlo-v2-row-main">
              <div className="phlo-v2-row-title">{emptyTitle}</div>
              <div className="phlo-v2-row-meta">{emptyBody}</div>
            </div>
          </div>
        )}
      </div>
      {result.error && (
        <div className="phlo-v2-panel-footer">
          <AlertCircle className="size-4" />
          <span>{result.error}</span>
        </div>
      )}
    </div>
  )
}

export function V2ResourceRow({ item }: { item: V2ResourceItem }) {
  const status = item.status ?? item.health?.state ?? item.kind

  return (
    <div className="phlo-v2-row">
      <div className="phlo-v2-row-main">
        <div className="phlo-v2-row-title">
          <span
            className="phlo-v2-dot"
            data-state={item.health?.state ?? item.status}
          />
          <span>{item.name}</span>
        </div>
        <div className="phlo-v2-row-meta">
          {item.summary ?? item.kind}
          {item.updated_at ? ` · ${item.updated_at}` : ''}
        </div>
      </div>
      <span className="phlo-v2-pill">{status}</span>
    </div>
  )
}

export function V2EmptyPanel({ title, body }: { title: string; body: string }) {
  return (
    <div className="phlo-v2-callout">
      <div className="phlo-v2-callout-title">{title}</div>
      <p className="phlo-v2-callout-body">{body}</p>
    </div>
  )
}

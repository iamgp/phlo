import type { ReactNode } from 'react'

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

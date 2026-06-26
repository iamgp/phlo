import type { ReactNode } from 'react'

export function ObservatoryPage({
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
    <div className="phlo-observatory-content">
      <header className="phlo-observatory-section-header">
        <div>
          <div className="phlo-observatory-kicker">{kicker}</div>
          <h1 className="phlo-observatory-title">{title}</h1>
          <p className="phlo-observatory-subtitle">{description}</p>
        </div>
        {action}
      </header>
      {children}
    </div>
  )
}

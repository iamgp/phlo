import { createFileRoute } from '@tanstack/react-router'

import { getObservatoryBiItems } from '@/observatory/api/resources'
import { ObservatorySurfacePage } from '@/observatory/components/ObservatorySurfacePage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/bi')({
  component: BI,
})

export function BI() {
  const result = useLiveResource(getObservatoryBiItems, 120_000, 'v2:bi')
  const items = result.data ?? []

  return (
    <ObservatorySurfacePage
      contract="/api/observatory/bi"
      description="Dashboards, reports, and analytics destinations connected to this project."
      emptyCopy="Analytics destinations will appear here when a BI package reports them."
      error={result.error}
      items={items}
      kicker="BI"
      title="BI surfaces"
    />
  )
}

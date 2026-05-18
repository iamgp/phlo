import { createFileRoute } from '@tanstack/react-router'

import { getV2BiItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/bi')({
  component: BI,
})

export function BI() {
  const result = useLiveResource(getV2BiItems, 120_000, 'v2:bi')
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/v2/bi"
      description="Dashboards, reports, and analytics destinations connected to this project."
      emptyCopy="Analytics destinations will appear here when a BI package reports them."
      error={result.error}
      items={items}
      kicker="BI"
      title="BI surfaces"
    />
  )
}

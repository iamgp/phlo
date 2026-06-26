import { createFileRoute } from '@tanstack/react-router'

import { getObservatoryApiItems } from '@/observatory/api/resources'
import { ObservatorySurfacePage } from '@/observatory/components/ObservatorySurfacePage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/apis')({
  component: APIs,
})

export function APIs() {
  const result = useLiveResource(getObservatoryApiItems, 120_000, 'v2:apis')
  const items = result.data ?? []

  return (
    <ObservatorySurfacePage
      contract="/api/observatory/apis"
      description="Published data APIs and backend services exposed by this stack."
      emptyCopy="Published APIs will appear here when a matching package reports them."
      error={result.error}
      items={items}
      kicker="APIs"
      title="API surfaces"
    />
  )
}

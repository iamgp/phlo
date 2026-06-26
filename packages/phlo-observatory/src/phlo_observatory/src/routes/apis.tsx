import { createFileRoute } from '@tanstack/react-router'

import { getV2ApiItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/apis')({
  component: APIs,
})

export function APIs() {
  const result = useLiveResource(getV2ApiItems, 120_000, 'v2:apis')
  const items = result.data ?? []

  return (
    <V2SurfacePage
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

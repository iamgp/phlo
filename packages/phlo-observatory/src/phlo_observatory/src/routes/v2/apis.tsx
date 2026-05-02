import { createFileRoute } from '@tanstack/react-router'

import { getV2ApiItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/apis')({
  component: APIs,
})

function APIs() {
  const result = useLiveResource(getV2ApiItems, 120_000, 'v2:apis')
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/v2/apis"
      description="Provider-neutral API backend and published data API surfaces."
      emptyCopy="API providers can add shallow published-surface summaries here before action or schema-management contracts are added."
      error={result.error}
      items={items}
      kicker="APIs"
      title="API surfaces"
    />
  )
}

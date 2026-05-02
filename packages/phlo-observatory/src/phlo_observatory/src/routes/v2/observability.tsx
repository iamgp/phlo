import { createFileRoute } from '@tanstack/react-router'

import { getV2ObservabilityItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/observability')({
  component: Observability,
})

function Observability() {
  const result = useLiveResource(
    getV2ObservabilityItems,
    120_000,
    'v2:observability',
  )
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/v2/observability"
      description="Provider-neutral telemetry, alerting, and monitoring surfaces."
      emptyCopy="Observability providers can add shallow telemetry summaries here without introducing backend-specific dashboards yet."
      error={result.error}
      items={items}
      kicker="Observability"
      title="Observability surfaces"
    />
  )
}

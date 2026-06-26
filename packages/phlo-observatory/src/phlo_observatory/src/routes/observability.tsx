import { createFileRoute } from '@tanstack/react-router'

import { getV2ObservabilityItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/observability')({
  component: Observability,
})

export function Observability() {
  const result = useLiveResource(
    getV2ObservabilityItems,
    120_000,
    'v2:observability',
  )
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/observability"
      description="Telemetry, alerting, and monitoring signals from the running stack."
      emptyCopy="Telemetry summaries will appear here when an observability package reports them."
      error={result.error}
      items={items}
      kicker="Observability"
      title="Observability surfaces"
    />
  )
}

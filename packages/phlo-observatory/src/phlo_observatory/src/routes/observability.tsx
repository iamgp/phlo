import { createFileRoute } from '@tanstack/react-router'

import { getObservatoryObservabilityItems } from '@/observatory/api/resources'
import { ObservatorySurfacePage } from '@/observatory/components/ObservatorySurfacePage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/observability')({
  component: Observability,
})

export function Observability() {
  const result = useLiveResource(
    getObservatoryObservabilityItems,
    120_000,
    'v2:observability',
  )
  const items = result.data ?? []

  return (
    <ObservatorySurfacePage
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

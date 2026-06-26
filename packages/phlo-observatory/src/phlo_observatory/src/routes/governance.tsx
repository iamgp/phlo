import { createFileRoute } from '@tanstack/react-router'

import { getObservatoryGovernanceItems } from '@/observatory/api/resources'
import { ObservatorySurfacePage } from '@/observatory/components/ObservatorySurfacePage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/governance')({
  component: Governance,
})

export function Governance() {
  const result = useLiveResource(getObservatoryGovernanceItems, 120_000, 'v2:governance')
  const items = result.data ?? []

  return (
    <ObservatorySurfacePage
      contract="/api/observatory/governance"
      description="Policies, ownership, identity, and compliance signals for this project."
      emptyCopy="Governance signals will appear here when a governance package reports them."
      error={result.error}
      items={items}
      kicker="Governance"
      title="Governance surfaces"
    />
  )
}

import { createFileRoute } from '@tanstack/react-router'

import { getV2GovernanceItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/governance')({
  component: Governance,
})

export function Governance() {
  const result = useLiveResource(getV2GovernanceItems, 120_000, 'v2:governance')
  const items = result.data ?? []

  return (
    <V2SurfacePage
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

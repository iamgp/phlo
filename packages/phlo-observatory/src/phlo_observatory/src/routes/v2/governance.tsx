import { createFileRoute } from '@tanstack/react-router'

import { getV2GovernanceItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/governance')({
  component: Governance,
})

export function Governance() {
  const result = useLiveResource(getV2GovernanceItems, 120_000, 'v2:governance')
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/v2/governance"
      description="Provider-neutral governance, policy, identity, and regulated-surface summaries."
      emptyCopy="Governance providers can add shallow summaries here before deeper policy editing or audit workflows exist."
      error={result.error}
      items={items}
      kicker="Governance"
      title="Governance surfaces"
    />
  )
}

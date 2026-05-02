import { createFileRoute } from '@tanstack/react-router'

import { Governance } from '@/routes/v2/governance'

export const Route = createFileRoute('/governance')({
  component: Governance,
})

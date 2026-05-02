import { createFileRoute } from '@tanstack/react-router'

import { Branches } from '@/routes/v2/branches'

export const Route = createFileRoute('/branches/')({
  component: Branches,
})

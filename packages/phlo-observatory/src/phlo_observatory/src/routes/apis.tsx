import { createFileRoute } from '@tanstack/react-router'

import { APIs } from '@/routes/v2/apis'

export const Route = createFileRoute('/apis')({
  component: APIs,
})

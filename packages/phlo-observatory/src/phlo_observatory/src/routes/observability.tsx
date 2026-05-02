import { createFileRoute } from '@tanstack/react-router'

import { Observability } from '@/routes/v2/observability'

export const Route = createFileRoute('/observability')({
  component: Observability,
})

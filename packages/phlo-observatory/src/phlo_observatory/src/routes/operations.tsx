import { createFileRoute } from '@tanstack/react-router'

import { Operations } from '@/routes/v2/operations'

export const Route = createFileRoute('/operations')({
  component: Operations,
})

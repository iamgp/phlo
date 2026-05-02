import { createFileRoute } from '@tanstack/react-router'

import { Runs } from '@/routes/v2/runs'

export const Route = createFileRoute('/runs')({
  component: Runs,
})

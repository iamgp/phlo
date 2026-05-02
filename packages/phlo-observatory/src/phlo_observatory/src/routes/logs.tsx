import { createFileRoute } from '@tanstack/react-router'

import { Logs } from '@/routes/v2/logs'

export const Route = createFileRoute('/logs')({
  component: Logs,
})

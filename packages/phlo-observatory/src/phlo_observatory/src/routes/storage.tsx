import { createFileRoute } from '@tanstack/react-router'

import { Storage } from '@/routes/v2/storage'

export const Route = createFileRoute('/storage')({
  component: Storage,
})

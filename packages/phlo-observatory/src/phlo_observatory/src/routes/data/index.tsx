import { createFileRoute } from '@tanstack/react-router'

import { Data } from '@/routes/v2/data'

export const Route = createFileRoute('/data/')({
  component: Data,
})

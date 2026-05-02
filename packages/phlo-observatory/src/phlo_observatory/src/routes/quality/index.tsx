import { createFileRoute } from '@tanstack/react-router'

import { Quality } from '@/routes/v2/quality'

export const Route = createFileRoute('/quality/')({
  component: Quality,
})

import { createFileRoute } from '@tanstack/react-router'

import { Services } from '@/routes/v2/services'

export const Route = createFileRoute('/services')({
  component: Services,
})

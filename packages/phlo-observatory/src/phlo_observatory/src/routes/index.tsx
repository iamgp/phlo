import { createFileRoute } from '@tanstack/react-router'

import { OverviewRoute } from '@/v2/routes/OverviewRoute'

export const Route = createFileRoute('/')({
  component: OverviewRoute,
})

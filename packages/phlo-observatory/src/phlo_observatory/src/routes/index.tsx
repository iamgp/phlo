import { createFileRoute } from '@tanstack/react-router'

import {
  OverviewRoute,
  loadOverviewSnapshot,
} from '@/observatory/routes/OverviewRoute'

export const Route = createFileRoute('/')({
  loader: loadOverviewSnapshot,
  component: ObservatoryIndexOverviewRoute,
})

function ObservatoryIndexOverviewRoute() {
  const snapshot = Route.useLoaderData()
  return <OverviewRoute initialSnapshot={snapshot} />
}

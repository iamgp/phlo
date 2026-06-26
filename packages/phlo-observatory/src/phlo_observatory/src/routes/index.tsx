import { createFileRoute } from '@tanstack/react-router'

import { OverviewRoute, loadOverviewSnapshot } from '@/v2/routes/OverviewRoute'

export const Route = createFileRoute('/')({
  loader: loadOverviewSnapshot,
  component: V2IndexOverviewRoute,
})

function V2IndexOverviewRoute() {
  const snapshot = Route.useLoaderData()
  return <OverviewRoute initialSnapshot={snapshot} />
}

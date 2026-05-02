import { createFileRoute } from '@tanstack/react-router'

import { TableDetailView } from '@/routes/v2/data/$tableId'

export const Route = createFileRoute('/table/$tableId')({
  component: TableDetailRoute,
})

function TableDetailRoute() {
  const { tableId } = Route.useParams()
  return <TableDetailView tableId={tableId} />
}

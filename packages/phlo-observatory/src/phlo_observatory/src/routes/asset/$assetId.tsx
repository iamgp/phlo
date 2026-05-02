import { createFileRoute } from '@tanstack/react-router'

import { AssetDetailView } from '@/routes/v2/assets/$assetId'

export const Route = createFileRoute('/asset/$assetId')({
  component: AssetDetailRoute,
})

function AssetDetailRoute() {
  const { assetId } = Route.useParams()
  return <AssetDetailView assetId={assetId} />
}

import { createFileRoute } from '@tanstack/react-router'

import { AssetDetailView } from '@/routes/v2/assets/$assetId'

export const Route = createFileRoute('/v2/asset/$assetId')({
  component: AssetDetailRoute,
})

function AssetDetailRoute() {
  const { assetId } = Route.useParams()
  return <AssetDetailView assetId={assetId} />
}

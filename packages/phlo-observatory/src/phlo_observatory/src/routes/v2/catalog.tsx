import { createFileRoute } from '@tanstack/react-router'

import { getV2CatalogItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/catalog')({
  component: Catalog,
})

export function Catalog() {
  const result = useLiveResource(getV2CatalogItems, 120_000, 'v2:catalog')
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/v2/catalog"
      description="Metadata catalogs and scanners connected to this project."
      emptyCopy="Catalog entries will appear here when a catalog package reports them."
      error={result.error}
      items={items}
      kicker="Catalog"
      title="Catalog surfaces"
    />
  )
}

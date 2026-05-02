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
      description="Provider-neutral metadata catalog and scanner surfaces."
      emptyCopy="Catalog providers can add shallow metadata summaries here without binding the UI to a catalog vendor."
      error={result.error}
      items={items}
      kicker="Catalog"
      title="Catalog surfaces"
    />
  )
}

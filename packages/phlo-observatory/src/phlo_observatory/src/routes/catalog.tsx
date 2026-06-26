import { createFileRoute } from '@tanstack/react-router'

import { getObservatoryCatalogItems } from '@/observatory/api/resources'
import { ObservatorySurfacePage } from '@/observatory/components/ObservatorySurfacePage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/catalog')({
  component: Catalog,
})

export function Catalog() {
  const result = useLiveResource(
    getObservatoryCatalogItems,
    120_000,
    'v2:catalog',
  )
  const items = result.data ?? []

  return (
    <ObservatorySurfacePage
      contract="/api/observatory/catalog"
      description="Metadata catalogs and scanners connected to this project."
      emptyCopy="Catalog entries will appear here when a catalog package reports them."
      error={result.error}
      items={items}
      kicker="Catalog"
      title="Catalog surfaces"
    />
  )
}

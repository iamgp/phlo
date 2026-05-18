import { createFileRoute } from '@tanstack/react-router'

import { getV2StorageItems } from '@/v2/api/resources'
import { V2SurfacePage } from '@/v2/components/V2SurfacePage'
import { useLiveResource } from '@/v2/routes/liveResource'

export const Route = createFileRoute('/v2/storage')({
  component: Storage,
})

export function Storage() {
  const result = useLiveResource(getV2StorageItems, 120_000, 'v2:storage')
  const items = result.data ?? []

  return (
    <V2SurfacePage
      contract="/api/observatory/v2/storage"
      description="Table stores, object stores, and storage services used by this project."
      emptyCopy="Storage resources will appear here when a storage package reports them."
      error={result.error}
      items={items}
      kicker="Storage"
      title="Storage surfaces"
    />
  )
}

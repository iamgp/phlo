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
      description="Provider-neutral table stores, object stores, and storage-facing lakehouse surfaces."
      emptyCopy="Storage providers can add shallow surface summaries here without coupling Observatory to a table format or object store adapter."
      error={result.error}
      items={items}
      kicker="Storage"
      title="Storage surfaces"
    />
  )
}

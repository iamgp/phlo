import { createFileRoute } from '@tanstack/react-router'

import { getObservatoryStorageItems } from '@/observatory/api/resources'
import { ObservatorySurfacePage } from '@/observatory/components/ObservatorySurfacePage'
import { useLiveResource } from '@/observatory/routes/liveResource'

export const Route = createFileRoute('/storage')({
  component: Storage,
})

export function Storage() {
  const result = useLiveResource(getObservatoryStorageItems, 120_000, 'v2:storage')
  const items = result.data ?? []

  return (
    <ObservatorySurfacePage
      contract="/api/observatory/storage"
      description="Table stores, object stores, and storage services used by this project."
      emptyCopy="Storage resources will appear here when a storage package reports them."
      error={result.error}
      items={items}
      kicker="Storage"
      title="Storage surfaces"
    />
  )
}

import { createFileRoute } from '@tanstack/react-router'

import { ExtensionDetailView } from '@/routes/v2/extensions/$extensionId'

export const Route = createFileRoute('/extension/$extensionId')({
  component: ExtensionDetailRoute,
})

function ExtensionDetailRoute() {
  const { extensionId } = Route.useParams()
  return <ExtensionDetailView extensionId={extensionId} />
}

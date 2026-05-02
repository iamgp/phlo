import { createFileRoute } from '@tanstack/react-router'

import { ExtensionDetailView } from '@/routes/v2/extensions/$extensionId'

export const Route = createFileRoute('/extensions/$extensionName')({
  component: ExtensionDetailRoute,
})

function ExtensionDetailRoute() {
  const { extensionName } = Route.useParams()
  return <ExtensionDetailView extensionId={extensionName} />
}

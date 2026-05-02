import { createFileRoute } from '@tanstack/react-router'

import { BranchDetailView } from '@/routes/v2/branches/$branchName'

export const Route = createFileRoute('/v2/branch/$branchName')({
  component: BranchDetailRoute,
})

function BranchDetailRoute() {
  const { branchName } = Route.useParams()
  return <BranchDetailView branchName={branchName} />
}

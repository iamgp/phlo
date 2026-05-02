import { createFileRoute } from '@tanstack/react-router'

import { BranchDetailView } from '@/routes/v2/branches/$branchName'

export const Route = createFileRoute('/branch/$branchName')({
  component: BranchDetailRoute,
})

function BranchDetailRoute() {
  const { branchName } = Route.useParams()
  return <BranchDetailView branchName={branchName} />
}

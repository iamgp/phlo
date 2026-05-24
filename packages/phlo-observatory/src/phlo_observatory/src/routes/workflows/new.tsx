import { createFileRoute } from '@tanstack/react-router'

import {
  WorkflowCanvasBuilder,
  loadWorkflowBuilderSnapshot,
} from '@/routes/v2/workflows/new'

export const Route = createFileRoute('/workflows/new')({
  loader: loadWorkflowBuilderSnapshot,
  component: WorkflowCanvasBuilderRoute,
})

function WorkflowCanvasBuilderRoute() {
  const snapshot = Route.useLoaderData()
  return <WorkflowCanvasBuilder initialSnapshot={snapshot} />
}

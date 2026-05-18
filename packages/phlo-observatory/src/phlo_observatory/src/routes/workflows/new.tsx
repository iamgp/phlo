import { createFileRoute } from '@tanstack/react-router'

import { WorkflowCanvasBuilder } from '@/routes/v2/workflows/new'

export const Route = createFileRoute('/workflows/new')({
  component: WorkflowCanvasBuilder,
})

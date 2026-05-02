import { createFileRoute } from '@tanstack/react-router'

import { BI } from '@/routes/v2/bi'

export const Route = createFileRoute('/bi')({
  component: BI,
})

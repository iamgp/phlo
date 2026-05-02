import { createFileRoute } from '@tanstack/react-router'

import { Assets } from '@/routes/v2/assets'

export const Route = createFileRoute('/assets/')({
  component: Assets,
})

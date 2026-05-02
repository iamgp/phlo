import { createFileRoute } from '@tanstack/react-router'

import { Extensions } from '@/routes/v2/extensions'

export const Route = createFileRoute('/extensions/')({
  component: Extensions,
})

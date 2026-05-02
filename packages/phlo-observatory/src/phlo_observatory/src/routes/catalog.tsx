import { createFileRoute } from '@tanstack/react-router'

import { Catalog } from '@/routes/v2/catalog'

export const Route = createFileRoute('/catalog')({
  component: Catalog,
})

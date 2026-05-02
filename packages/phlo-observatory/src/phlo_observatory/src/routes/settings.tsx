import { createFileRoute } from '@tanstack/react-router'

import { SettingsRoute } from '@/routes/v2/settings'

export const Route = createFileRoute('/settings')({
  component: SettingsRoute,
})

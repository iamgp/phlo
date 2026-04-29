import { Outlet, createFileRoute } from '@tanstack/react-router'

import { V2Shell } from '@/v2/shell/V2Shell'

export const Route = createFileRoute('/v2')({
  component: V2Layout,
})

function V2Layout() {
  return (
    <V2Shell>
      <Outlet />
    </V2Shell>
  )
}

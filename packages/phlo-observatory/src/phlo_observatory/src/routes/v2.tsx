import { Outlet, createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/v2')({
  component: V2Layout,
})

function V2Layout() {
  return <Outlet />
}

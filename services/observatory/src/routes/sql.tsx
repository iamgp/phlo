import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/sql')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/sql"!</div>
}

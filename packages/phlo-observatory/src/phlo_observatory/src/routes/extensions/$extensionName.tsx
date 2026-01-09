import { createFileRoute, createRoute } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'
import type { ComponentType } from 'react'

import { useObservatoryExtensions } from '@/extensions/registry'
import { Route as RootRoute } from '@/routes/__root'
import { getObservatoryExtensions } from '@/server/extensions.server'

export const Route = createFileRoute('/extensions/$extensionName')({
  component: ExtensionPage,
})

type LoadedState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; Component: ComponentType }
  | { status: 'error'; message: string }

function ExtensionPage() {
  const { extensionName } = Route.useParams()
  const registry = useObservatoryExtensions()
  const [state, setState] = useState<LoadedState>({ status: 'idle' })

  const routeEntry = useMemo(() => {
    const extension = registry.extensions.find(
      (entry) => entry.manifest.name === extensionName,
    )
    const routes = extension?.manifest.ui?.routes ?? []
    const target = `/extensions/${extensionName}`
    return (
      routes.find((route) => route.path === target) ??
      routes.find((route) => route.path.startsWith(`${target}/`)) ??
      routes[0]
    )
  }, [extensionName, registry.extensions])

  useEffect(() => {
    if (typeof window === 'undefined') return

    const load = async () => {
      let target = routeEntry

      if (!target) {
        try {
          const extensions = await getObservatoryExtensions()
          const extension = extensions.find(
            (entry) => entry.manifest.name === extensionName,
          )
          const routes = extension?.manifest.ui?.routes ?? []
          const expected = `/extensions/${extensionName}`
          target =
            routes.find((route) => route.path === expected) ??
            routes.find((route) => route.path.startsWith(`${expected}/`)) ??
            routes[0]
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : 'Failed to load extension manifest.'
          setState({ status: 'error', message })
          return
        }
      }

      if (!target) {
        setState({
          status: 'error',
          message: 'No extension route registered.',
        })
        return
      }

      setState({ status: 'loading' })

      try {
        const module = await import(/* @vite-ignore */ target.module)
        const registerRoutes = module[target.export] as
          | ((ctx: {
              createRoute: typeof createRoute
              rootRoute: typeof RootRoute
            }) => unknown)
          | undefined

        if (typeof registerRoutes !== 'function') {
          setState({
            status: 'error',
            message: 'Extension route export missing or invalid.',
          })
          return
        }

        const result = registerRoutes({
          createRoute,
          rootRoute: RootRoute,
        })
        const routes = Array.isArray(result) ? result : result ? [result] : []
        const match = routes.find(
          (route) => route.options?.path === target.path,
        )
        const Component = match?.options?.component

        if (!Component) {
          setState({
            status: 'error',
            message: 'Extension route component not found.',
          })
          return
        }

        setState({ status: 'ready', Component })
      } catch (error) {
        const message =
          error instanceof Error ? error.message : 'Failed to load extension.'
        setState({ status: 'error', message })
      }
    }

    void load()
  }, [extensionName, routeEntry])

  if (state.status === 'ready') {
    const Component = state.Component
    return <Component />
  }

  if (state.status === 'error') {
    return (
      <div className="p-6">
        <h1 className="text-xl font-semibold">Extension failed to load</h1>
        <p className="text-muted-foreground">{state.message}</p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold">Loading extension...</h1>
    </div>
  )
}

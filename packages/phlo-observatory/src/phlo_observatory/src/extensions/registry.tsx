import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { createRoute, useRouter } from '@tanstack/react-router'
import type { ComponentType, ReactNode } from 'react'
import type { AnyRoute } from '@tanstack/react-router'

import type {
  ObservatoryExtension,
  ObservatoryExtensionNavItem,
  ObservatoryExtensionRoute,
} from '@/server/extensions.server'
import { getObservatoryExtensions } from '@/server/extensions.server'

export type ExtensionRouteContext = {
  createRoute: typeof createRoute
  rootRoute: AnyRoute
  extensionName: string
  route: ObservatoryExtensionRoute
}

export type RegisterRoutesFn = (
  ctx: ExtensionRouteContext,
) => AnyRoute | Array<AnyRoute> | void

export type SlotRegistry = {
  register: (slotId: string, component: ComponentType) => void
}

export type RegisterSlotFn = (registry: SlotRegistry) => void

type ExtensionRegistryState = {
  extensions: Array<ObservatoryExtension>
  navItems: Array<ObservatoryExtensionNavItem>
  slots: Record<string, Array<ComponentType>>
}

const ExtensionRegistryContext = createContext<ExtensionRegistryState | null>(
  null,
)

function uniqueNavItems(items: Array<ObservatoryExtensionNavItem>) {
  const seen = new Set<string>()
  return items.filter((item) => {
    const key = `${item.title}:${item.to}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

export function ObservatoryExtensionProvider({
  children,
}: {
  children: ReactNode
}) {
  const router = useRouter()
  const [extensions, setExtensions] = useState<Array<ObservatoryExtension>>([])
  const [navItems, setNavItems] = useState<Array<ObservatoryExtensionNavItem>>(
    [],
  )
  const [slots, setSlots] = useState<Record<string, Array<ComponentType>>>({})
  const registeredExtensions = useRef(new Set<string>())

  useEffect(() => {
    if (typeof window === 'undefined') return

    let active = true

    const registerSlot: SlotRegistry['register'] = (slotId, component) => {
      setSlots((current) => ({
        ...current,
        [slotId]: [...(current[slotId] ?? []), component],
      }))
    }

    const loadExtensions = async () => {
      let entries: Array<ObservatoryExtension>
      try {
        entries = await getObservatoryExtensions()
      } catch {
        return
      }
      if (!active) return

      setExtensions(entries)
      const nextNavItems = uniqueNavItems(
        entries.flatMap((entry) => entry.manifest.ui?.nav ?? []),
      )
      setNavItems(nextNavItems)

      const rootRoute = router.options.routeTree as AnyRoute | undefined
      const nextRoutes: Array<AnyRoute> = []

      if (!rootRoute) return

      for (const extension of entries) {
        const extensionName = extension.manifest.name
        if (registeredExtensions.current.has(extensionName)) {
          continue
        }
        registeredExtensions.current.add(extensionName)

        const routes = extension.manifest.ui?.routes ?? []
        for (const route of routes) {
          try {
            const module = await import(/* @vite-ignore */ route.module)
            const registerRoutes = module[route.export] as
              | RegisterRoutesFn
              | undefined
            if (typeof registerRoutes !== 'function') continue
            const result = registerRoutes({
              createRoute,
              rootRoute,
              extensionName,
              route,
            })
            if (Array.isArray(result)) {
              nextRoutes.push(...result)
            } else if (result) {
              nextRoutes.push(result)
            }
          } catch {
            continue
          }
        }

        const slotsToRegister = extension.manifest.ui?.slots ?? []
        for (const slot of slotsToRegister) {
          try {
            const module = await import(/* @vite-ignore */ slot.module)
            const registerSlotFn = module[slot.export] as
              | RegisterSlotFn
              | undefined
            if (typeof registerSlotFn !== 'function') continue
            registerSlotFn({ register: registerSlot })
          } catch {
            continue
          }
        }
      }

      if (nextRoutes.length) {
        const nextRouteTree = rootRoute.addChildren(nextRoutes)
        router.update({
          ...router.options,
          routeTree: nextRouteTree as typeof router.options.routeTree,
        })
      }
    }

    void loadExtensions()

    return () => {
      active = false
    }
  }, [router])

  const value = useMemo<ExtensionRegistryState>(
    () => ({ extensions, navItems, slots }),
    [extensions, navItems, slots],
  )

  return (
    <ExtensionRegistryContext.Provider value={value}>
      {children}
    </ExtensionRegistryContext.Provider>
  )
}

export function useObservatoryExtensions() {
  const value = useContext(ExtensionRegistryContext)
  if (!value) {
    throw new Error(
      'useObservatoryExtensions must be used within ObservatoryExtensionProvider',
    )
  }
  return value
}

export function ExtensionSlot({
  slotId,
  className,
}: {
  slotId: string
  className?: string
}) {
  const { slots } = useObservatoryExtensions()
  const components = slots[slotId] ?? []

  if (!components.length) return null

  return (
    <div className={className}>
      {components.map((Component, index) => (
        <Component key={`${slotId}-${index}`} />
      ))}
    </div>
  )
}

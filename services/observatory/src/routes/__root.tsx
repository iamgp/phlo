import { TanStackDevtools } from '@tanstack/react-devtools'
import {
  HeadContent,
  Link,
  Outlet,
  Scripts,
  createRootRoute,
} from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'

import appCss from '../styles.css?url'
import type { ResolvedTheme, ThemeMode } from '@/components/ThemeToggle'
import type { Asset } from '@/server/dagster.server'
import { AppSidebar } from '@/components/AppSidebar'
import { CommandPalette } from '@/components/CommandPalette'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button, buttonVariants } from '@/components/ui/button'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import {
  ObservatorySettingsProvider,
  useObservatorySettings,
} from '@/hooks/useObservatorySettings'
import { cn } from '@/lib/utils'
import { getAssets } from '@/server/dagster.server'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'Phlo Observatory' },
      {
        name: 'description',
        content: 'Unified visibility into your data platform',
      },
    ],
    links: [
      { rel: 'stylesheet', href: appCss },
      { rel: 'icon', href: '/favicon.ico' },
    ],
  }),

  component: RootLayout,
  notFoundComponent: NotFound,
})

const THEME_STORAGE_KEY = 'phlo-observatory-theme'

function RootLayout() {
  return (
    <ObservatorySettingsProvider>
      <RootLayoutInner />
    </ObservatorySettingsProvider>
  )
}

function RootLayoutInner() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [assets, setAssets] = useState<Array<Asset>>([])
  const [themeMode, setThemeMode] = useState<ThemeMode>('system')
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>('dark')
  const { settings } = useObservatorySettings()

  // Load assets for command palette
  useEffect(() => {
    getAssets({
      data: { dagsterUrl: settings.connections.dagsterGraphqlUrl },
    }).then((result) => {
      if (!('error' in result)) {
        setAssets(result)
      }
    })
  }, [settings.connections.dagsterGraphqlUrl])

  // Ensure we don't have a stale PWA/service worker controlling the app (dev-only).
  // This can happen if the app previously ran with Vite PWA/Workbox and will cause 404s
  // for old entrypoints (e.g. /main.tsx, /manifest.webmanifest).
  useEffect(() => {
    if (!import.meta.env.DEV) return
    if (!('serviceWorker' in navigator)) return

    void navigator.serviceWorker.getRegistrations().then((registrations) => {
      void Promise.all(registrations.map((r) => r.unregister()))
    })

    if ('caches' in window) {
      void caches
        .keys()
        .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
    }
  }, [])

  // Theme: light/dark/system persisted in localStorage.
  useEffect(() => {
    if (typeof window === 'undefined') return

    const stored = window.localStorage.getItem(
      THEME_STORAGE_KEY,
    ) as ThemeMode | null
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      setThemeMode(stored)
    }

    const media = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!media) return

    const update = () => setSystemTheme(media.matches ? 'dark' : 'light')
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(THEME_STORAGE_KEY, themeMode)
  }, [themeMode])

  const resolvedTheme: ResolvedTheme =
    themeMode === 'system' ? systemTheme : themeMode

  return (
    <html
      lang="en"
      className={resolvedTheme === 'dark' ? 'dark' : ''}
      data-density={settings.ui.density}
      suppressHydrationWarning
    >
      <head>
        <HeadContent />
      </head>
      <body className="h-svh overflow-hidden bg-background text-foreground">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-14 items-center gap-2 border-b bg-sidebar px-4">
              <SidebarTrigger />
              <div className="ml-auto flex items-center gap-2">
                <ThemeToggle
                  mode={themeMode}
                  resolvedTheme={resolvedTheme}
                  onModeChange={setThemeMode}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCommandPaletteOpen(true)}
                >
                  <Search className="size-4" />
                  Search
                  <span className="text-muted-foreground ml-2 hidden sm:inline">
                    ⌘K
                  </span>
                </Button>
              </div>
            </header>
            <div className="flex-1 overflow-hidden min-h-0">
              <Outlet />
            </div>
          </SidebarInset>
        </SidebarProvider>

        <CommandPalette
          assets={assets}
          open={commandPaletteOpen}
          onOpenChange={setCommandPaletteOpen}
        />
        <TanStackDevtools
          config={{ position: 'bottom-right' }}
          plugins={[
            {
              name: 'TanStack Router',
              render: <TanStackRouterDevtoolsPanel />,
            },
          ]}
        />
        <Scripts />
      </body>
    </html>
  )
}

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found</p>
      <Link to="/" className={cn(buttonVariants({ size: 'sm' }))}>
        Go Home
      </Link>
    </div>
  )
}

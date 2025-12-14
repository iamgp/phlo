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
import type { Asset } from '@/server/dagster.server'
import type { ResolvedTheme, ThemeMode } from '@/components/ThemeToggle'
import { AppSidebar } from '@/components/AppSidebar'
import { CommandPalette } from '@/components/CommandPalette'
import { Button, buttonVariants } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { getAssets } from '@/server/dagster.server'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '@/components/ThemeToggle'

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
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [assets, setAssets] = useState<Array<Asset>>([])
  const [themeMode, setThemeMode] = useState<ThemeMode>('system')
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>('dark')

  // Load assets for command palette
  useEffect(() => {
    getAssets().then((result) => {
      if (!('error' in result)) {
        setAssets(result)
      }
    })
  }, [])

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
      suppressHydrationWarning
    >
      <head>
        <HeadContent />
      </head>
      <body className="min-h-screen bg-background text-foreground">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-14 items-center gap-2 border-b px-4">
              <SidebarTrigger />
              <Separator orientation="vertical" className="h-6 self-center" />
              <div className="flex items-center gap-2">
                <Link to="/" className="text-sm font-semibold tracking-tight">
                  Phlo Observatory
                </Link>
              </div>
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
            <div className="flex-1 overflow-auto">
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

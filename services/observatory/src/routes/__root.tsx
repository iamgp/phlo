import { TanStackDevtools } from '@tanstack/react-devtools'
import {
  HeadContent,
  Link,
  Outlet,
  Scripts,
  createRootRoute,
} from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import {
  Activity,
  Database,
  GitBranch,
  LayoutDashboard,
  Search,
  Settings,
  Shield,
  Table,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import appCss from '../styles.css?url'
import type {Asset} from '@/server/dagster.server';
import { CommandPalette } from '@/components/CommandPalette'
import {  getAssets } from '@/server/dagster.server'

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

function RootLayout() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [assets, setAssets] = useState<Array<Asset>>([])

  // Load assets for command palette
  useEffect(() => {
    getAssets().then((result) => {
      if (!('error' in result)) {
        setAssets(result)
      }
    })
  }, [])

  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body className="bg-slate-900 text-slate-100 min-h-screen">
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
            {/* Logo */}
            <div className="h-[72px] px-4 border-b border-slate-700 flex items-center">
              <Link to="/" className="flex items-center gap-2">
                <Activity className="w-8 h-8 text-cyan-400" />
                <span className="text-xl font-bold">Phlo Observatory</span>
              </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4">
              <ul className="space-y-2">
                <NavItem
                  to="/"
                  icon={<LayoutDashboard size={20} />}
                  label="Dashboard"
                />
                <NavItem
                  to="/data"
                  icon={<Table size={20} />}
                  label="Data Explorer"
                />
                <NavItem
                  to="/assets"
                  icon={<Database size={20} />}
                  label="Assets"
                />
                <NavItem
                  to="/graph"
                  icon={<GitBranch size={20} />}
                  label="Lineage Graph"
                />
                <NavItem
                  to="/branches"
                  icon={<GitBranch size={20} />}
                  label="Branches"
                />
                <NavItem
                  to="/quality"
                  icon={<Shield size={20} />}
                  label="Quality"
                />
                <NavItem
                  to="/search"
                  icon={<Search size={20} />}
                  label="Search"
                  disabled
                />
                <NavItem
                  to="/settings"
                  icon={<Settings size={20} />}
                  label="Settings"
                  disabled
                />
              </ul>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-slate-700 text-sm text-slate-500">
              Phase 4 • v0.0.4
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <Outlet />
          </main>
        </div>

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

interface NavItemProps {
  to: string
  icon: React.ReactNode
  label: string
  disabled?: boolean
}

function NavItem({ to, icon, label, disabled }: NavItemProps) {
  if (disabled) {
    return (
      <li>
        <span className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-500 cursor-not-allowed">
          {icon}
          <span>{label}</span>
          <span className="ml-auto text-xs bg-slate-700 px-1.5 py-0.5 rounded">
            Soon
          </span>
        </span>
      </li>
    )
  }

  return (
    <li>
      <Link
        to={to}
        className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-700 transition-colors"
        activeProps={{
          className:
            'flex items-center gap-3 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-700 transition-colors',
        }}
      >
        {icon}
        <span>{label}</span>
      </Link>
    </li>
  )
}

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h1 className="text-4xl font-bold text-slate-300 mb-4">404</h1>
      <p className="text-slate-400 mb-6">Page not found</p>
      <Link
        to="/"
        className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg transition-colors"
      >
        Go Home
      </Link>
    </div>
  )
}

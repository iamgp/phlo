import { Link, useRouterState } from '@tanstack/react-router'
import {
  Activity,
  Boxes,
  Database,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  Logs,
  Monitor,
  Moon,
  Plug,
  Search,
  Server,
  Settings,
  Sun,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2Capabilities,
  V2CapabilityPage,
  V2ResourceResult,
  V2SearchResult,
} from '@/v2/api/types'
import type { V2ThemeMode } from '@/v2/shell/theme'
import {
  V2_THEME_STORAGE_KEY,
  readV2ThemeMode,
  resolveV2Theme,
} from '@/v2/shell/theme'
import { getV2Capabilities, searchV2 } from '@/v2/api/resources'

const fallbackPages: Array<V2CapabilityPage> = [
  corePage('overview', 'Overview', '/v2'),
  corePage('services', 'Services', '/v2/services'),
  corePage('settings', 'Settings', '/v2/settings'),
]

const iconByPageId: Record<string, typeof LayoutDashboard> = {
  overview: LayoutDashboard,
  services: Server,
  operations: Activity,
  data: Database,
  assets: Boxes,
  issues: ListChecks,
  quality: ListChecks,
  logs: Logs,
  branches: GitBranch,
  extensions: Plug,
  settings: Settings,
}

const themeModes = [
  { mode: 'system', label: 'System', icon: Monitor },
  { mode: 'light', label: 'Light', icon: Sun },
  { mode: 'dark', label: 'Dark', icon: Moon },
] satisfies Array<{
  mode: V2ThemeMode
  label: string
  icon: typeof Monitor
}>

export function V2Shell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const [searchOpen, setSearchOpen] = useState(false)
  const [themeMode, setThemeMode] = useState<V2ThemeMode>('system')
  const [systemPrefersDark, setSystemPrefersDark] = useState(false)
  const [hydrated, setHydrated] = useState(false)
  const [query, setQuery] = useState('')
  const [capabilities, setCapabilities] =
    useState<V2ResourceResult<V2Capabilities> | null>(null)
  const [results, setResults] = useState<
    V2ResourceResult<Array<V2SearchResult>>
  >({
    data: null,
    error: null,
  })
  const resolvedTheme = resolveV2Theme(themeMode, systemPrefersDark)
  const pages = hydrated
    ? (capabilities?.data?.pages ?? fallbackPages)
    : fallbackPages
  const navItems = pages.filter((page) => page.nav && page.available)
  const activePage = pageForPath(pathname, pages)
  const pageUnavailable =
    hydrated &&
    capabilities?.data !== null &&
    activePage !== null &&
    activePage.available === false

  useEffect(() => {
    setHydrated(true)
    setThemeMode(readV2ThemeMode(window.localStorage))

    const media = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!media) return

    const update = () => setSystemPrefersDark(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    window.localStorage.setItem(V2_THEME_STORAGE_KEY, themeMode)
  }, [themeMode])

  useEffect(() => {
    document.documentElement.dataset.phloV2Route = 'true'
    document.documentElement.dataset.phloV2Theme = resolvedTheme
    document.documentElement.style.colorScheme = resolvedTheme

    return () => {
      delete document.documentElement.dataset.phloV2Route
      delete document.documentElement.dataset.phloV2Theme
      document.documentElement.style.removeProperty('color-scheme')
    }
  }, [resolvedTheme])

  useEffect(() => {
    let cancelled = false
    async function load() {
      const next = await getV2Capabilities()
      if (!cancelled) setCapabilities(next)
    }
    void load()
    const interval = window.setInterval(load, 30_000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    if (!searchOpen || query.trim().length < 2) {
      setResults({ data: null, error: null })
      return
    }
    let cancelled = false
    const timer = window.setTimeout(() => {
      void searchV2({ data: { query } }).then((next) => {
        if (!cancelled) setResults(next)
      })
    }, 180)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [query, searchOpen])

  return (
    <main
      className="phlo-v2"
      data-theme={resolvedTheme}
      data-theme-mode={themeMode}
      suppressHydrationWarning
    >
      <div className="phlo-v2-nav-bar">
        <nav className="phlo-v2-shell phlo-v2-nav" aria-label="Observatory v2">
          <div className="phlo-v2-brand">
            <span className="phlo-v2-mark">P</span>
            <span>Phlo Observatory</span>
          </div>
          <div className="phlo-v2-nav-links">
            {navItems.map((item) => {
              const Icon = iconByPageId[item.id] ?? LayoutDashboard
              return (
                <Link
                  key={item.id}
                  to={item.path}
                  className="phlo-v2-nav-link"
                  data-active={isActive(pathname, item.path)}
                  title={
                    item.providers.length
                      ? item.providers.join(', ')
                      : undefined
                  }
                >
                  <Icon className="size-3.5" />
                  {item.label}
                </Link>
              )
            })}
            <button
              className="phlo-v2-nav-link"
              onClick={() => setSearchOpen((open) => !open)}
              type="button"
            >
              <Search className="size-3.5" />
              Search
            </button>
            <div className="phlo-v2-theme-toggle" aria-label="Theme">
              {themeModes.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    aria-label={`${item.label} theme`}
                    aria-pressed={themeMode === item.mode}
                    data-active={themeMode === item.mode}
                    key={item.mode}
                    onClick={() => setThemeMode(item.mode)}
                    suppressHydrationWarning
                    title={`${item.label} theme`}
                    type="button"
                  >
                    <Icon className="size-3.5" />
                  </button>
                )
              })}
            </div>
          </div>
        </nav>
      </div>
      <div className="phlo-v2-shell phlo-v2-body">
        {searchOpen && (
          <div className="phlo-v2-search-popover">
            <label className="phlo-v2-search-field">
              <Search className="size-4" />
              <input
                aria-label="Search Observatory"
                autoFocus
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search services, assets, tables, checks"
                value={query}
              />
            </label>
            <div className="phlo-v2-search-results">
              {(results.data ?? []).map((result) => (
                <Link
                  className="phlo-v2-search-result"
                  key={result.id}
                  onClick={() => setSearchOpen(false)}
                  to={result.href ?? '/v2'}
                >
                  <span>{result.label}</span>
                  <small>
                    {[result.kind, result.summary].filter(Boolean).join(' · ')}
                  </small>
                </Link>
              ))}
              {query.trim().length >= 2 && results.data?.length === 0 && (
                <p>No matches.</p>
              )}
              {results.error && <p>{results.error}</p>}
            </div>
          </div>
        )}
        <section className="phlo-v2-sheet">
          {pageUnavailable ? <UnavailablePage page={activePage} /> : children}
        </section>
      </div>
    </main>
  )
}

function isActive(pathname: string, href: string): boolean {
  if (href === '/v2') return pathname === '/v2'
  return pathname === href || pathname.startsWith(`${href}/`)
}

function pageForPath(
  pathname: string,
  pages: Array<V2CapabilityPage>,
): V2CapabilityPage | null {
  const exact = pages.find((page) => pathname === page.path)
  if (exact) return exact

  const aliases: Record<string, string> = {
    '/v2/table/': 'data',
    '/v2/data/': 'data',
    '/v2/asset/': 'assets',
    '/v2/assets/': 'assets',
    '/v2/branch/': 'branches',
    '/v2/branches/': 'branches',
    '/v2/extension/': 'extensions',
    '/v2/extensions/': 'extensions',
  }
  const match = Object.entries(aliases).find(([prefix]) =>
    pathname.startsWith(prefix),
  )
  if (!match) return null
  return pages.find((page) => page.id === match[1]) ?? null
}

function UnavailablePage({ page }: { page: V2CapabilityPage }) {
  return (
    <div className="phlo-v2-content">
      <header className="phlo-v2-section-header">
        <div>
          <div className="phlo-v2-kicker">Capability unavailable</div>
          <h1 className="phlo-v2-title">{page.label}</h1>
          <p className="phlo-v2-subtitle">
            {page.reason ??
              'This surface is hidden until a provider contributes data for it.'}
          </p>
        </div>
      </header>
      <section className="phlo-v2-panel phlo-v2-empty-panel">
        <h2>Nothing to control here yet</h2>
        <p>
          Install or enable the matching Phlo package, then Observatory will add
          this page automatically.
        </p>
      </section>
    </div>
  )
}

function corePage(id: string, label: string, path: string): V2CapabilityPage {
  return {
    id,
    label,
    path,
    available: true,
    nav: true,
    providers: [],
    metadata: {},
  }
}

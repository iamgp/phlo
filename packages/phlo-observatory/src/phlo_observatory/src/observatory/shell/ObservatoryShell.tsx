import { Link, useRouterState } from '@tanstack/react-router'
import {
  Activity,
  Boxes,
  CirclePlay,
  Clipboard,
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
import { Suspense, lazy, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  ObservatoryCapabilities,
  ObservatoryCapabilityPage,
  ObservatoryResourceResult,
  ObservatoryTable,
} from '@/observatory/api/types'
import type { ObservatoryThemeMode } from '@/observatory/shell/theme'
import {
  OBSERVATORY_THEME_STORAGE_KEY,
  readObservatoryThemeMode,
  resolveObservatoryTheme,
} from '@/observatory/shell/theme'
import {
  getObservatoryAssetRecords,
  getObservatoryCapabilities,
  getObservatoryLogRecords,
  getObservatoryQualityRecords,
  getObservatoryRunRecords,
  getObservatoryServices,
  getObservatoryTablePreview,
  getObservatoryTableRecords,
} from '@/observatory/api/resources'
import { loadCachedResource } from '@/observatory/routes/liveResource'

const ObservatoryCommandPalette = lazy(() =>
  import('@/observatory/shell/ObservatoryCommandPalette').then((module) => ({
    default: module.ObservatoryCommandPalette,
  })),
)

const fallbackPages: Array<ObservatoryCapabilityPage> = [
  corePage('overview', 'Overview', '/'),
  corePage('operations', 'Operations', '/operations'),
  corePage('data', 'Data', '/data'),
  corePage('assets', 'Assets', '/assets'),
  corePage('workflows', 'Workflows', '/workflows/new'),
  corePage('issues', 'Issues', '/quality'),
  corePage('branches', 'Changes', '/branches'),
  corePage('logs', 'Logs', '/logs'),
  corePage('services', 'Services', '/services'),
  corePage('settings', 'Settings', '/settings'),
]

const navOrder = [
  'overview',
  'operations',
  'data',
  'assets',
  'workflows',
  'runs',
  'issues',
  'quality',
  'branches',
  'storage',
  'observability',
  'logs',
  'governance',
  'catalog',
  'apis',
  'bi',
  'extensions',
  'services',
  'settings',
]

const warmPreviewLimit = 100

const iconByPageId: Record<string, typeof LayoutDashboard> = {
  overview: LayoutDashboard,
  services: Server,
  operations: Activity,
  runs: CirclePlay,
  data: Database,
  assets: Boxes,
  workflows: Clipboard,
  issues: ListChecks,
  quality: ListChecks,
  logs: Logs,
  branches: GitBranch,
  extensions: Plug,
  storage: Database,
  observability: Activity,
  governance: Settings,
  catalog: Boxes,
  apis: Server,
  bi: LayoutDashboard,
  settings: Settings,
}

const themeModes = [
  { mode: 'system', label: 'System', icon: Monitor },
  { mode: 'light', label: 'Light', icon: Sun },
  { mode: 'dark', label: 'Dark', icon: Moon },
] satisfies Array<{
  mode: ObservatoryThemeMode
  label: string
  icon: typeof Monitor
}>

export function ObservatoryShell(props: { children: ReactNode }) {
  return useObservatoryShell(props)
}

function useObservatoryShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const [searchOpen, setSearchOpen] = useState(false)
  const [{ hydrated, systemPrefersDark, themeMode }, setThemeState] = useState({
    hydrated: false,
    systemPrefersDark: false,
    themeMode: 'system' as ObservatoryThemeMode,
  })
  const [capabilities, setCapabilities] =
    useState<ObservatoryResourceResult<ObservatoryCapabilities> | null>(null)
  const resolvedTheme = resolveObservatoryTheme(themeMode, systemPrefersDark)
  const pages = hydrated
    ? (capabilities?.data?.pages ?? fallbackPages)
    : fallbackPages
  const navItems = pages
    .filter((page) => page.nav && page.available)
    .sort((left, right) => navRank(left.id) - navRank(right.id))
  const activePage = pageForPath(pathname, pages)
  const pagePending = capabilities === null && activePage === null
  const pageUnavailable =
    hydrated &&
    capabilities?.data !== null &&
    activePage !== null &&
    activePage.available === false

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)')
    setThemeState({
      hydrated: true,
      systemPrefersDark: media?.matches ?? false,
      themeMode: readObservatoryThemeMode(window.localStorage),
    })
    if (!media) return

    const update = () =>
      setThemeState((current) => ({
        ...current,
        systemPrefersDark: media.matches,
      }))
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!hydrated) return
    window.localStorage.setItem(OBSERVATORY_THEME_STORAGE_KEY, themeMode)
  }, [hydrated, themeMode])

  useEffect(() => {
    document.documentElement.dataset.phloObservatoryRoute = 'true'
    document.documentElement.dataset.phloObservatoryTheme = resolvedTheme
    document.documentElement.style.colorScheme = resolvedTheme

    return () => {
      delete document.documentElement.dataset.phloObservatoryRoute
      delete document.documentElement.dataset.phloObservatoryTheme
      document.documentElement.style.removeProperty('color-scheme')
    }
  }, [resolvedTheme])

  useEffect(() => {
    let cancelled = false
    async function load() {
      if (cancelled) return
      const next = await loadCachedResource(
        'v2:capabilities',
        getObservatoryCapabilities,
        { force: true, staleMs: 30_000 },
      )
      if (!cancelled) {
        setCapabilities(next)
        warmRouteResources(next.data)
      }
    }
    void load()
    const interval = window.setInterval(load, 30_000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const isCommandSearch =
        event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey)
      if (isCommandSearch) {
        event.preventDefault()
        setSearchOpen(true)
        return
      }
      if (event.key === 'Escape' && searchOpen) {
        event.preventDefault()
        setSearchOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [searchOpen])

  return (
    <main
      className="phlo-observatory"
      data-theme={resolvedTheme}
      data-theme-mode={themeMode}
      suppressHydrationWarning
    >
      <div className="phlo-observatory-nav-bar">
        <nav
          className="phlo-observatory-shell phlo-observatory-nav"
          aria-label="Observatory"
        >
          <div className="phlo-observatory-brand">
            <span className="phlo-observatory-mark">P</span>
            <span>Phlo Observatory</span>
          </div>
          <div
            className="phlo-observatory-nav-links"
            aria-label="Primary sections"
          >
            {navItems.map((item) => {
              const Icon = iconByPageId[item.id] ?? LayoutDashboard
              return (
                <Link
                  aria-current={
                    hydrated && isActive(pathname, item.path)
                      ? 'page'
                      : undefined
                  }
                  className="phlo-observatory-nav-link"
                  data-active={hydrated && isActive(pathname, item.path)}
                  key={item.id}
                  title={
                    hydrated && item.providers.length
                      ? item.providers.join(', ')
                      : undefined
                  }
                  to={item.path}
                >
                  <Icon className="size-3.5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
          <div className="phlo-observatory-nav-actions">
            <button
              aria-expanded={searchOpen}
              aria-haspopup="dialog"
              className="phlo-observatory-nav-link phlo-observatory-search-trigger"
              onClick={() => setSearchOpen(true)}
              type="button"
            >
              <Search className="size-3.5" />
              <span>Search</span>
              <kbd>⌘K</kbd>
            </button>
            <div className="phlo-observatory-theme-toggle" aria-label="Theme">
              {themeModes.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    aria-label={`${item.label} theme`}
                    aria-pressed={themeMode === item.mode}
                    data-active={themeMode === item.mode}
                    key={item.mode}
                    onClick={() =>
                      setThemeState((current) => ({
                        ...current,
                        themeMode: item.mode,
                      }))
                    }
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
      <div className="phlo-observatory-shell phlo-observatory-body">
        {searchOpen && (
          <Suspense
            fallback={
              <CommandPaletteFallback onClose={() => setSearchOpen(false)} />
            }
          >
            <ObservatoryCommandPalette
              navItems={navItems}
              onClose={() => setSearchOpen(false)}
            />
          </Suspense>
        )}
        <div className="phlo-observatory-app-layout">
          <section className="phlo-observatory-sheet">
            {pagePending ? (
              <PendingCapabilityPage />
            ) : pageUnavailable ? (
              <UnavailablePage page={activePage} />
            ) : (
              children
            )}
          </section>
        </div>
      </div>
    </main>
  )
}

function isActive(pathname: string, href: string): boolean {
  const cleanPathname = cleanPath(pathname)
  const cleanHref = cleanPath(href)
  if (cleanPathname === '/graph' && cleanHref === '/assets') return true
  if (cleanHref === '/') return cleanPathname === '/'
  return (
    cleanPathname === cleanHref || cleanPathname.startsWith(`${cleanHref}/`)
  )
}

function CommandPaletteFallback({ onClose }: { onClose: () => void }) {
  return (
    <div
      aria-label="Command search"
      aria-modal="true"
      className="phlo-observatory-command-overlay"
      role="dialog"
    >
      <button
        aria-label="Close search"
        className="phlo-observatory-command-backdrop"
        onClick={onClose}
        type="button"
      />
      <div className="phlo-observatory-search-popover">
        <div className="phlo-observatory-command phlo-observatory-command-palette">
          <div className="phlo-observatory-search-field">
            <Search className="size-4" />
            <span>Loading search…</span>
            <kbd>Esc</kbd>
          </div>
        </div>
      </div>
    </div>
  )
}

function navRank(pageId: string): number {
  const index = navOrder.indexOf(pageId)
  return index === -1 ? navOrder.length : index
}

function pageForPath(
  pathname: string,
  pages: Array<ObservatoryCapabilityPage>,
): ObservatoryCapabilityPage | null {
  const cleanPathname = cleanPath(pathname)
  const exact = pages.find((page) => cleanPathname === cleanPath(page.path))
  if (exact) return exact

  const aliases: Record<string, string> = {
    '/data/': 'data',
    '/assets/': 'assets',
    '/branches/': 'branches',
    '/extensions/': 'extensions',
  }
  const match = Object.entries(aliases).find(([prefix]) =>
    cleanPathname.startsWith(prefix),
  )
  if (!match) return null
  return pages.find((page) => page.id === match[1]) ?? null
}

function cleanPath(path: string): string {
  return path
}

function warmRouteResources(capabilities: ObservatoryCapabilities | null) {
  if (!capabilities) return
  const features = capabilities.features
  void loadCachedResource('v2:services', getObservatoryServices, {
    staleMs: 120_000,
  })
  if (features.data) {
    void loadCachedResource('v2:tables', getObservatoryTableRecords, {
      staleMs: 120_000,
    }).then((result) => warmDefaultTablePreview(result.data ?? []))
  }
  if (features.assets) {
    void loadCachedResource('v2:assets', getObservatoryAssetRecords, {
      staleMs: 120_000,
    })
  }
  if (features.runs) {
    void loadCachedResource('v2:runs', getObservatoryRunRecords, {
      staleMs: 120_000,
    })
  }
  if (features.issues || features.quality) {
    void loadCachedResource('v2:quality', getObservatoryQualityRecords, {
      staleMs: 120_000,
    })
  }
  if (features.logs) {
    void loadCachedResource('v2:logs', getObservatoryLogRecords, {
      staleMs: 120_000,
    })
  }
}

function warmDefaultTablePreview(tables: Array<ObservatoryTable>) {
  const table = choosePreviewTable(tables)
  if (!table) return
  void loadCachedResource(
    `v2:table-preview:${table.id}:${warmPreviewLimit}:0:0`,
    () =>
      getObservatoryTablePreview({
        data: { tableId: table.id, limit: warmPreviewLimit, offset: 0 },
      }),
    { staleMs: 120_000 },
  )
}

function choosePreviewTable(
  tables: Array<ObservatoryTable>,
): ObservatoryTable | null {
  return (
    tables.find((table) => isQueryableTable(table) && hasRowCount(table)) ??
    tables.find(
      (table) => isQueryableTable(table) && tableLane(table) === 'silver',
    ) ??
    tables.find(isQueryableTable) ??
    tables.find((table) => tableLane(table) === 'silver') ??
    tables[0] ??
    null
  )
}

function isQueryableTable(table: ObservatoryTable): boolean {
  const state = table.metadata.catalog_state
  if (state === 'queryable') return true
  if (state === 'model_only') return false
  return table.metadata.catalog_present === true
}

function hasRowCount(table: ObservatoryTable): boolean {
  return (
    table.metadata.rows !== undefined ||
    table.metadata.records !== undefined ||
    table.metadata.row_count !== undefined
  )
}

function tableLane(table: ObservatoryTable): string {
  return String(table.namespace ?? table.schema_name ?? '').toLowerCase()
}

function PendingCapabilityPage() {
  return (
    <div className="phlo-observatory-content">
      <header className="phlo-observatory-section-header">
        <div>
          <div className="phlo-observatory-kicker">Checking capability</div>
          <h1 className="phlo-observatory-title">Loading surface</h1>
          <p className="phlo-observatory-subtitle">
            Observatory is checking the project packages before opening this
            page.
          </p>
        </div>
      </header>
      <section className="phlo-observatory-panel phlo-observatory-empty-panel">
        <h2>Reading project capabilities</h2>
        <p>Pages appear here only when the matching provider is installed.</p>
      </section>
    </div>
  )
}

function UnavailablePage({ page }: { page: ObservatoryCapabilityPage }) {
  return (
    <div className="phlo-observatory-content">
      <header className="phlo-observatory-section-header">
        <div>
          <div className="phlo-observatory-kicker">Capability unavailable</div>
          <h1 className="phlo-observatory-title">{page.label}</h1>
          <p className="phlo-observatory-subtitle">
            {page.reason ??
              'This surface is hidden until a provider contributes data for it.'}
          </p>
        </div>
      </header>
      <section className="phlo-observatory-panel phlo-observatory-empty-panel">
        <h2>Nothing to control here yet</h2>
        <p>
          Install or enable the matching Phlo package, then Observatory will add
          this page automatically.
        </p>
      </section>
    </div>
  )
}

function corePage(
  id: string,
  label: string,
  path: string,
): ObservatoryCapabilityPage {
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

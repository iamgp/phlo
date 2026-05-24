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
  V2Capabilities,
  V2CapabilityPage,
  V2ResourceResult,
  V2Table,
} from '@/v2/api/types'
import type { V2ThemeMode } from '@/v2/shell/theme'
import {
  V2_THEME_STORAGE_KEY,
  readV2ThemeMode,
  resolveV2Theme,
} from '@/v2/shell/theme'
import {
  getV2AssetRecords,
  getV2Capabilities,
  getV2LogRecords,
  getV2QualityRecords,
  getV2RunRecords,
  getV2Services,
  getV2TablePreview,
  getV2TableRecords,
} from '@/v2/api/resources'
import { loadCachedResource } from '@/v2/routes/liveResource'

const V2CommandPalette = lazy(() =>
  import('@/v2/shell/V2CommandPalette').then((module) => ({
    default: module.V2CommandPalette,
  })),
)

const fallbackPages: Array<V2CapabilityPage> = [
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
  mode: V2ThemeMode
  label: string
  icon: typeof Monitor
}>

export function V2Shell(props: { children: ReactNode }) {
  return useV2Shell(props)
}

function useV2Shell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const [searchOpen, setSearchOpen] = useState(false)
  const [{ hydrated, systemPrefersDark, themeMode }, setThemeState] = useState({
    hydrated: false,
    systemPrefersDark: false,
    themeMode: 'system' as V2ThemeMode,
  })
  const [capabilities, setCapabilities] =
    useState<V2ResourceResult<V2Capabilities> | null>(null)
  const resolvedTheme = resolveV2Theme(themeMode, systemPrefersDark)
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
      themeMode: readV2ThemeMode(window.localStorage),
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
    window.localStorage.setItem(V2_THEME_STORAGE_KEY, themeMode)
  }, [hydrated, themeMode])

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
      if (cancelled) return
      const next = await loadCachedResource(
        'v2:capabilities',
        getV2Capabilities,
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
          <div className="phlo-v2-nav-links" aria-label="Primary sections">
            {navItems.map((item) => {
              const Icon = iconByPageId[item.id] ?? LayoutDashboard
              return (
                <Link
                  aria-current={
                    hydrated && isActive(pathname, item.path)
                      ? 'page'
                      : undefined
                  }
                  className="phlo-v2-nav-link"
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
          <div className="phlo-v2-nav-actions">
            <button
              aria-expanded={searchOpen}
              aria-haspopup="dialog"
              className="phlo-v2-nav-link phlo-v2-search-trigger"
              onClick={() => setSearchOpen(true)}
              type="button"
            >
              <Search className="size-3.5" />
              <span>Search</span>
              <kbd>⌘K</kbd>
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
      <div className="phlo-v2-shell phlo-v2-body">
        {searchOpen && (
          <Suspense
            fallback={
              <CommandPaletteFallback onClose={() => setSearchOpen(false)} />
            }
          >
            <V2CommandPalette
              navItems={navItems}
              onClose={() => setSearchOpen(false)}
            />
          </Suspense>
        )}
        <div className="phlo-v2-app-layout">
          <section className="phlo-v2-sheet">
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
      className="phlo-v2-command-overlay"
      role="dialog"
    >
      <button
        aria-label="Close search"
        className="phlo-v2-command-backdrop"
        onClick={onClose}
        type="button"
      />
      <div className="phlo-v2-search-popover">
        <div className="phlo-v2-command phlo-v2-command-palette">
          <div className="phlo-v2-search-field">
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
  pages: Array<V2CapabilityPage>,
): V2CapabilityPage | null {
  const cleanPathname = cleanPath(pathname)
  const exact = pages.find((page) => cleanPathname === cleanPath(page.path))
  if (exact) return exact

  const aliases: Record<string, string> = {
    '/table/': 'data',
    '/data/': 'data',
    '/asset/': 'assets',
    '/assets/': 'assets',
    '/branch/': 'branches',
    '/branches/': 'branches',
    '/extension/': 'extensions',
    '/extensions/': 'extensions',
  }
  const match = Object.entries(aliases).find(([prefix]) =>
    cleanPathname.startsWith(prefix),
  )
  if (!match) return null
  return pages.find((page) => page.id === match[1]) ?? null
}

function cleanPath(path: string): string {
  if (path === '/v2') return '/'
  if (path.startsWith('/v2/')) return path.slice(3) || '/'
  return path
}

function warmRouteResources(capabilities: V2Capabilities | null) {
  if (!capabilities) return
  const features = capabilities.features
  void loadCachedResource('v2:services', getV2Services, { staleMs: 120_000 })
  if (features.data) {
    void loadCachedResource('v2:tables', getV2TableRecords, {
      staleMs: 120_000,
    }).then((result) => warmDefaultTablePreview(result.data ?? []))
  }
  if (features.assets) {
    void loadCachedResource('v2:assets', getV2AssetRecords, {
      staleMs: 120_000,
    })
  }
  if (features.runs) {
    void loadCachedResource('v2:runs', getV2RunRecords, { staleMs: 120_000 })
  }
  if (features.issues || features.quality) {
    void loadCachedResource('v2:quality', getV2QualityRecords, {
      staleMs: 120_000,
    })
  }
  if (features.logs) {
    void loadCachedResource('v2:logs', getV2LogRecords, { staleMs: 120_000 })
  }
}

function warmDefaultTablePreview(tables: Array<V2Table>) {
  const table = choosePreviewTable(tables)
  if (!table) return
  void loadCachedResource(
    `v2:table-preview:${table.id}:${warmPreviewLimit}:0:0`,
    () =>
      getV2TablePreview({
        data: { tableId: table.id, limit: warmPreviewLimit, offset: 0 },
      }),
    { staleMs: 120_000 },
  )
}

function choosePreviewTable(tables: Array<V2Table>): V2Table | null {
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

function isQueryableTable(table: V2Table): boolean {
  const state = table.metadata.catalog_state
  if (state === 'queryable') return true
  if (state === 'model_only') return false
  return table.metadata.catalog_present === true
}

function hasRowCount(table: V2Table): boolean {
  return (
    table.metadata.rows !== undefined ||
    table.metadata.records !== undefined ||
    table.metadata.row_count !== undefined
  )
}

function tableLane(table: V2Table): string {
  return String(table.namespace ?? table.schema_name ?? '').toLowerCase()
}

function PendingCapabilityPage() {
  return (
    <div className="phlo-v2-content">
      <header className="phlo-v2-section-header">
        <div>
          <div className="phlo-v2-kicker">Checking capability</div>
          <h1 className="phlo-v2-title">Loading surface</h1>
          <p className="phlo-v2-subtitle">
            Observatory is checking the project packages before opening this
            page.
          </p>
        </div>
      </header>
      <section className="phlo-v2-panel phlo-v2-empty-panel">
        <h2>Reading project capabilities</h2>
        <p>Pages appear here only when the matching provider is installed.</p>
      </section>
    </div>
  )
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

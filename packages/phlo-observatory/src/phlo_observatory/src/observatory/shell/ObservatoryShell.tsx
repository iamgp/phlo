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
  UploadCloud,
} from 'lucide-react'
import { Suspense, lazy, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from '@/components/ui/navigation-menu'
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
  getObservatoryDataProductRecords,
  getObservatoryGovernanceItems,
  getObservatoryLogRecords,
  getObservatoryPipelineRecords,
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
  corePage('issues', 'Quality', '/quality'),
  corePage('branches', 'Changes', '/branches'),
  corePage('catalog', 'Catalog', '/catalog'),
  corePage('governance', 'Governance', '/governance'),
  corePage('publishing', 'Publishing', '/publishing'),
  corePage('pipelines', 'Pipelines', '/pipelines'),
  corePage('logs', 'Logs', '/logs'),
  corePage('services', 'Services', '/services'),
  corePage('settings', 'Settings', '/settings'),
]

const navOrder = [
  'overview',
  'catalog',
  'governance',
  'publishing',
  'apis',
  'bi',
  'data',
  'assets',
  'storage',
  'branches',
  'issues',
  'quality',
  'pipelines',
  'runs',
  'operations',
  'logs',
  'workflows',
  'observability',
  'services',
  'extensions',
  'settings',
]

const navGroupDefinitions = [
  {
    label: 'Catalog',
    ids: ['catalog', 'governance', 'publishing', 'apis', 'bi'],
  },
  {
    label: 'Tables',
    ids: ['data', 'assets', 'storage', 'branches'],
  },
  {
    label: 'Quality',
    ids: ['issues', 'quality'],
  },
  {
    label: 'Operations',
    ids: [
      'pipelines',
      'runs',
      'operations',
      'logs',
      'workflows',
      'observability',
    ],
  },
  {
    label: 'Platform',
    ids: ['overview', 'services', 'extensions', 'settings'],
  },
] satisfies Array<{ label: string; ids: Array<string> }>

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
  publishing: UploadCloud,
  pipelines: Activity,
  apis: Server,
  bi: LayoutDashboard,
  settings: Settings,
}

const navSubtitleByPageId: Record<string, string> = {
  overview: 'Health, counters, and recent activity.',
  services: 'Runtime services and stack status.',
  operations: 'Jobs, actions, and run state.',
  runs: 'Orchestrator history and outcomes.',
  data: 'Tables, previews, and query surfaces.',
  assets: 'Lineage, dependencies, and metadata.',
  storage: 'Lakehouse storage and branches.',
  observability: 'Signals from metrics and traces.',
  logs: 'Platform and resource events.',
  catalog: 'Promoted products and raw candidates.',
  governance: 'Owners, classifications, controls.',
  publishing: 'Internal release readiness.',
  pipelines: 'Product flow and freshness.',
  workflows: 'Create and edit Phlo workflows.',
  issues: 'Checks needing attention.',
  quality: 'Checks, severity, and evidence.',
  branches: 'Changes, reviews, and WAP context.',
  apis: 'Published API surfaces.',
  bi: 'Reports, dashboards, and consumers.',
  extensions: 'Installed providers and settings.',
  settings: 'Project and Observatory preferences.',
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
    ? mergeFallbackPages(capabilities?.data?.pages ?? fallbackPages)
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
    activePage.available === false &&
    !isFallbackPage(activePage.id)

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
          <Link
            aria-label="Home"
            className="phlo-observatory-brand"
            title="Home"
            to="/"
          >
            <span className="phlo-observatory-mark">P</span>
            <span>Phlo Observatory</span>
          </Link>
          <div
            className="phlo-observatory-nav-links"
            aria-label="Primary sections"
          >
            <ObservatoryNavigationMenu
              hydrated={hydrated}
              items={navItems}
              pathname={pathname}
            />
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

function ObservatoryNavigationMenu({
  hydrated,
  items,
  pathname,
}: {
  hydrated: boolean
  items: Array<ObservatoryCapabilityPage>
  pathname: string
}) {
  const groups = navGroups(items)
  return (
    <NavigationMenu align="center" className="phlo-observatory-menu">
      <NavigationMenuList className="phlo-observatory-menu-list">
        {groups.map((group) => {
          const active = group.items.some((item) =>
            isActive(pathname, item.path),
          )
          return (
            <NavigationMenuItem key={group.label}>
              <NavigationMenuTrigger
                className="phlo-observatory-nav-link phlo-observatory-menu-trigger"
                data-active={hydrated && active}
              >
                {group.label}
              </NavigationMenuTrigger>
              <NavigationMenuContent>
                <div className="phlo-observatory-menu-panel">
                  <ul className="phlo-observatory-menu-grid">
                    {group.items.map((item) => {
                      const Icon = iconByPageId[item.id] ?? LayoutDashboard
                      const activeItem =
                        hydrated && isActive(pathname, item.path)
                      return (
                        <li key={item.id}>
                          <NavigationMenuLink
                            render={
                              <Link
                                aria-current={activeItem ? 'page' : undefined}
                                data-active={activeItem}
                                title={
                                  hydrated && item.providers.length
                                    ? item.providers.join(', ')
                                    : undefined
                                }
                                to={item.path}
                              />
                            }
                            className="phlo-observatory-menu-link"
                          >
                            <Icon className="size-4" />
                            <span className="phlo-observatory-menu-copy">
                              <span>{item.label}</span>
                              <span className="phlo-observatory-menu-subtitle">
                                {navSubtitleByPageId[item.id] ??
                                  'Open this Observatory surface.'}
                              </span>
                            </span>
                          </NavigationMenuLink>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              </NavigationMenuContent>
            </NavigationMenuItem>
          )
        })}
      </NavigationMenuList>
    </NavigationMenu>
  )
}

function navGroups(items: Array<ObservatoryCapabilityPage>) {
  const byId = new Map(items.map((item) => [item.id, item]))
  const used = new Set<string>()
  const groups = navGroupDefinitions
    .map((group) => {
      const groupItems = group.ids.flatMap((id) => {
        const item = byId.get(id)
        if (!item) return []
        used.add(id)
        return [item]
      })
      return { label: group.label, items: groupItems }
    })
    .filter((group) => group.items.length > 0)
  const rest = items.filter((item) => !used.has(item.id))
  return rest.length ? [...groups, { label: 'More', items: rest }] : groups
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

function mergeFallbackPages(
  pages: Array<ObservatoryCapabilityPage>,
): Array<ObservatoryCapabilityPage> {
  const merged = new Map(pages.map((page) => [page.id, page]))
  for (const fallback of fallbackPages) {
    const page = merged.get(fallback.id)
    merged.set(
      fallback.id,
      page ? { ...page, available: true, nav: true } : fallback,
    )
  }
  return Array.from(merged.values())
}

function isFallbackPage(pageId: string): boolean {
  return fallbackPages.some((page) => page.id === pageId)
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
    '/data-products/': 'catalog',
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
  if (features.catalog || features.publishing) {
    void loadCachedResource(
      'v2:data-products',
      getObservatoryDataProductRecords,
      {
        staleMs: 120_000,
      },
    )
  }
  if (features.governance) {
    void loadCachedResource(
      'v2:governance-matrix',
      getObservatoryGovernanceItems,
      {
        staleMs: 120_000,
      },
    )
  }
  if (features.pipelines) {
    void loadCachedResource('v2:pipelines', getObservatoryPipelineRecords, {
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
  const providers = page.providers.length ? page.providers.join(', ') : 'none'

  return (
    <div className="phlo-observatory-content">
      <header className="phlo-observatory-section-header">
        <div>
          <div className="phlo-observatory-kicker">
            Capability not connected
          </div>
          <h1 className="phlo-observatory-title">{page.label}</h1>
          <p className="phlo-observatory-subtitle">
            {page.reason ??
              'This surface appears when a project package contributes data for it.'}
          </p>
        </div>
      </header>
      <section className="phlo-observatory-panel phlo-observatory-empty-panel phlo-observatory-capability-panel">
        <div>
          <h2>{page.label} is not available in this stack</h2>
          <p>
            Keep working in the connected Observatory areas, or add the package
            that provides this read model when the project needs it.
          </p>
        </div>
        <dl className="phlo-observatory-capability-grid">
          <dt>Status</dt>
          <dd>not connected</dd>
          <dt>Providers</dt>
          <dd>{providers}</dd>
          <dt>Next step</dt>
          <dd>enable matching package</dd>
        </dl>
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

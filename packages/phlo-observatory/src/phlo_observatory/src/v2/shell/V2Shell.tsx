import { Link, useNavigate, useRouterState } from '@tanstack/react-router'
import { Command as CommandPrimitive } from 'cmdk'
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
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'

import type {
  V2Capabilities,
  V2CapabilityPage,
  V2ResourceResult,
  V2SearchResult,
  V2Service,
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
  searchV2,
} from '@/v2/api/resources'
import { loadCachedResource } from '@/v2/routes/liveResource'

const fallbackPages: Array<V2CapabilityPage> = [
  corePage('overview', 'Overview', '/'),
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
const commandGroupLimit = 6

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
  const navigate = useNavigate()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const [searchOpen, setSearchOpen] = useState(false)
  const [{ hydrated, systemPrefersDark, themeMode }, setThemeState] = useState({
    hydrated: false,
    systemPrefersDark: false,
    themeMode: 'system' as V2ThemeMode,
  })
  const [query, setQuery] = useState('')
  const searchInputRef = useRef<HTMLInputElement | null>(null)
  const [capabilities, setCapabilities] =
    useState<V2ResourceResult<V2Capabilities> | null>(null)
  const [results, setResults] = useState<
    V2ResourceResult<Array<V2SearchResult>>
  >({
    data: null,
    error: null,
  })
  const [commandTables, setCommandTables] = useState<
    V2ResourceResult<Array<V2Table>>
  >({
    data: null,
    error: null,
  })
  const [commandServices, setCommandServices] = useState<
    V2ResourceResult<Array<V2Service>>
  >({
    data: null,
    error: null,
  })
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
        { staleMs: 120_000 },
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

  useEffect(() => {
    if (!searchOpen) return
    let cancelled = false
    void Promise.all([
      loadCachedResource('v2:tables', getV2TableRecords, {
        staleMs: 120_000,
      }),
      loadCachedResource('v2:services', getV2Services, {
        staleMs: 120_000,
      }),
    ]).then(([tables, services]) => {
      if (cancelled) return
      setCommandTables(tables)
      setCommandServices(services)
    })
    return () => {
      cancelled = true
    }
  }, [searchOpen])

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

  useEffect(() => {
    if (!searchOpen) return
    const timer = window.setTimeout(() => searchInputRef.current?.focus(), 0)
    return () => window.clearTimeout(timer)
  }, [searchOpen])

  const closeSearch = useCallback(() => {
    setSearchOpen(false)
    setQuery('')
  }, [])

  const handleCommandSelect = useCallback(
    (value: string) => {
      if (value.startsWith('copy-sql:')) {
        const tableId = value.replace('copy-sql:', '')
        const sql = `select * from ${tableId} limit 100`
        void navigator.clipboard?.writeText(sql)
        closeSearch()
        return
      }

      const href = value.replace('open:', '')
      closeSearch()
      void navigate({ to: href })
    },
    [closeSearch, navigate],
  )

  const groupedResults = useMemo(() => {
    const groups = new Map<string, Array<V2SearchResult>>()
    const excludedKinds = new Set(['service', 'table', 'dataset'])
    for (const result of results.data ?? []) {
      if (excludedKinds.has(result.kind)) continue
      const key = result.kind || 'result'
      const group = groups.get(key)
      if (group) {
        group.push(result)
      } else {
        groups.set(key, [result])
      }
    }
    return Array.from(groups.entries())
  }, [results.data])

  const tableResults = useMemo(
    () =>
      (results.data ?? []).filter(
        (result) => result.kind === 'table' || result.kind === 'dataset',
      ),
    [results.data],
  )

  const tableMatches = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const tables = commandTables.data ?? []
    if (!needle) return tables.slice(0, 12)

    return tables
      .filter((table) =>
        [
          table.id,
          table.name,
          tableLabel(table),
          table.namespace,
          table.schema_name,
          table.branch,
          table.format,
          table.asset_id,
          table.metadata.table,
          table.metadata.table_name,
          table.metadata.schema,
          table.metadata.database,
          table.metadata.catalog,
          table.metadata.relation,
          table.metadata.materialized,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(needle)),
      )
      .slice(0, 16)
  }, [commandTables.data, query])

  const serviceMatches = useMemo(() => {
    const needle = query.trim().toLowerCase()
    const services = commandServices.data ?? []
    if (!needle) return services.slice(0, 12)

    return services
      .filter((service) =>
        [
          service.id,
          service.name,
          service.kind,
          service.status,
          service.profile,
          service.backend,
          service.health.state,
          service.health.message,
          service.metadata.description,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(needle)),
      )
      .slice(0, 16)
  }, [commandServices.data, query])

  const pageMatches = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return navItems
    return navItems.filter((item) =>
      [item.id, item.label, item.path, ...item.providers]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle)),
    )
  }, [navItems, query])

  const hasLocalMatches =
    pageMatches.length > 0 ||
    tableMatches.length > 0 ||
    serviceMatches.length > 0
  const sqlTemplateTargets = tableMatches.length
    ? tableMatches
    : tableResults.slice(0, 6).flatMap((result) => {
        const table = tableFromSearchResult(result)
        return table ? [table] : []
      })

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
          <div
            aria-label="Command search"
            aria-modal="true"
            className="phlo-v2-command-overlay"
            role="dialog"
          >
            <button
              aria-label="Close search"
              className="phlo-v2-command-backdrop"
              onClick={() => setSearchOpen(false)}
              type="button"
            />
            <div className="phlo-v2-search-popover">
              <CommandPrimitive
                className="phlo-v2-command phlo-v2-command-palette"
                loop
                shouldFilter={false}
              >
                <div className="phlo-v2-search-field">
                  <Search className="size-4" />
                  <CommandPrimitive.Input
                    aria-label="Search Observatory"
                    id="phlo-v2-command-input"
                    onKeyDown={(event) => {
                      if (event.key === 'Escape') {
                        event.preventDefault()
                        setSearchOpen(false)
                      }
                    }}
                    onValueChange={setQuery}
                    placeholder="Search services, assets, tables, checks"
                    ref={searchInputRef}
                    value={query}
                  />
                  <kbd>Esc</kbd>
                </div>
                <CommandPrimitive.List className="phlo-v2-command-list">
                  {query.trim().length >= 2 && pageMatches.length > 0 && (
                    <CommandPrimitive.Group
                      className="phlo-v2-command-group"
                      heading={`Pages (${pageMatches.length})`}
                    >
                      {pageMatches.slice(0, commandGroupLimit).map((item) => {
                        const Icon = iconByPageId[item.id] ?? LayoutDashboard
                        return (
                          <CommandPrimitive.Item
                            className="phlo-v2-command-item"
                            key={`nav:${item.id}`}
                            onSelect={handleCommandSelect}
                            value={`open:${item.path}`}
                          >
                            <Icon className="size-4" />
                            <span>{item.label}</span>
                            <small>{item.providers.join(', ') || 'core'}</small>
                          </CommandPrimitive.Item>
                        )
                      })}
                    </CommandPrimitive.Group>
                  )}

                  {query.trim().length < 2 && (
                    <CommandPrimitive.Group
                      className="phlo-v2-command-group"
                      heading="Fast actions"
                    >
                      <CommandPrimitive.Item
                        className="phlo-v2-command-item"
                        onSelect={handleCommandSelect}
                        value="open:/data"
                      >
                        <Database className="size-4" />
                        <span>Browse tables</span>
                        <small>Data</small>
                      </CommandPrimitive.Item>
                      <CommandPrimitive.Item
                        className="phlo-v2-command-item"
                        onSelect={handleCommandSelect}
                        value="open:/assets"
                      >
                        <Boxes className="size-4" />
                        <span>Inspect assets and lineage</span>
                        <small>Assets</small>
                      </CommandPrimitive.Item>
                      <CommandPrimitive.Item
                        className="phlo-v2-command-item"
                        onSelect={handleCommandSelect}
                        value="open:/runs"
                      >
                        <CirclePlay className="size-4" />
                        <span>Review orchestration runs</span>
                        <small>Runs</small>
                      </CommandPrimitive.Item>
                    </CommandPrimitive.Group>
                  )}

                  {query.trim().length >= 2 && tableMatches.length > 0 && (
                    <CommandPrimitive.Group
                      className="phlo-v2-command-group"
                      heading={`Tables (${tableMatches.length})`}
                    >
                      {tableMatches.slice(0, commandGroupLimit).map((table) => (
                        <CommandPrimitive.Item
                          className="phlo-v2-command-item"
                          key={`table:${table.id}`}
                          onSelect={handleCommandSelect}
                          value={`open:/table/${encodeURIComponent(table.id)}`}
                        >
                          <Database className="size-4" />
                          <span>{tableLabel(table)}</span>
                          <small>
                            {table.branch ?? table.format ?? 'table'}
                          </small>
                        </CommandPrimitive.Item>
                      ))}
                      {tableMatches.length > commandGroupLimit && (
                        <CommandPrimitive.Item
                          className="phlo-v2-command-item"
                          onSelect={handleCommandSelect}
                          value="open:/data"
                        >
                          <Database className="size-4" />
                          <span>Open table browser</span>
                          <small>{tableMatches.length} matches</small>
                        </CommandPrimitive.Item>
                      )}
                    </CommandPrimitive.Group>
                  )}

                  {query.trim().length >= 2 && serviceMatches.length > 0 && (
                    <CommandPrimitive.Group
                      className="phlo-v2-command-group"
                      heading={`Services (${serviceMatches.length})`}
                    >
                      {serviceMatches
                        .slice(0, commandGroupLimit)
                        .map((service) => (
                          <CommandPrimitive.Item
                            className="phlo-v2-command-item"
                            key={`service:${service.id}`}
                            onSelect={handleCommandSelect}
                            value="open:/services"
                          >
                            <Server className="size-4" />
                            <span>{service.name}</span>
                            <small>
                              {[service.kind, service.status]
                                .filter(Boolean)
                                .join(' · ')}
                            </small>
                          </CommandPrimitive.Item>
                        ))}
                      {serviceMatches.length > commandGroupLimit && (
                        <CommandPrimitive.Item
                          className="phlo-v2-command-item"
                          onSelect={handleCommandSelect}
                          value="open:/services"
                        >
                          <Server className="size-4" />
                          <span>Open service directory</span>
                          <small>{serviceMatches.length} matches</small>
                        </CommandPrimitive.Item>
                      )}
                    </CommandPrimitive.Group>
                  )}

                  {groupedResults.map(([kind, items]) => (
                    <CommandPrimitive.Group
                      className="phlo-v2-command-group"
                      heading={`${commandHeading(kind)} (${items.length})`}
                      key={kind}
                    >
                      {items.slice(0, commandGroupLimit).map((result) => (
                        <CommandPrimitive.Item
                          className="phlo-v2-command-item"
                          key={result.id}
                          onSelect={handleCommandSelect}
                          value={`open:${cleanPath(result.href ?? '/')}`}
                        >
                          {iconForSearchKind(result.kind)}
                          <span>{result.label}</span>
                          <small>{result.summary ?? result.kind}</small>
                        </CommandPrimitive.Item>
                      ))}
                    </CommandPrimitive.Group>
                  ))}

                  {query.trim().length >= 2 &&
                    sqlTemplateTargets.length > 0 && (
                      <CommandPrimitive.Group
                        className="phlo-v2-command-group"
                        heading="SQL templates"
                      >
                        {sqlTemplateTargets.slice(0, 4).map((table) => (
                          <CommandPrimitive.Item
                            className="phlo-v2-command-item"
                            key={`sql:${table.id}`}
                            onSelect={handleCommandSelect}
                            value={`copy-sql:${table.id}`}
                          >
                            <Clipboard className="size-4" />
                            <span>Copy SELECT from {tableLabel(table)}</span>
                            <small>Read-only template</small>
                          </CommandPrimitive.Item>
                        ))}
                      </CommandPrimitive.Group>
                    )}

                  {query.trim().length >= 2 &&
                    results.data?.length === 0 &&
                    !hasLocalMatches && (
                      <CommandPrimitive.Empty className="phlo-v2-command-empty">
                        No results found.
                      </CommandPrimitive.Empty>
                    )}
                  {results.error && (
                    <div className="phlo-v2-command-empty">{results.error}</div>
                  )}
                </CommandPrimitive.List>
                <div className="phlo-v2-command-footer">
                  <span>↑↓ navigate</span>
                  <span>↵ select</span>
                  <span>esc close</span>
                </div>
              </CommandPrimitive>
            </div>
          </div>
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

function commandHeading(kind: string): string {
  const labels: Record<string, string> = {
    asset: 'Assets',
    table: 'Tables',
    service: 'Services',
    log: 'Logs',
    operation: 'Operations',
    branch: 'Branches',
    extension: 'Extensions',
    run: 'Runs',
    quality: 'Quality',
    setting: 'Settings',
  }
  return labels[kind] ?? kind
}

function iconForSearchKind(kind: string): ReactNode {
  if (kind === 'asset') return <Boxes className="size-4" />
  if (kind === 'table') return <Database className="size-4" />
  if (kind === 'service') return <Server className="size-4" />
  if (kind === 'log') return <Logs className="size-4" />
  if (kind === 'branch') return <GitBranch className="size-4" />
  if (kind === 'run') return <CirclePlay className="size-4" />
  return <Search className="size-4" />
}

function tableLabel(table: V2Table): string {
  const namespace = table.namespace ?? table.schema_name
  if (!namespace) return table.name
  return `${namespace}.${table.name}`
}

function tableFromSearchResult(result: V2SearchResult): V2Table | null {
  if (!['table', 'dataset'].includes(result.kind)) return null
  const id = result.id.replace(/^table:/, '').replace(/^dataset:/, '')
  const labelParts = result.label.split('.')
  const name = labelParts.at(-1) ?? id
  const namespace =
    labelParts.length > 1 ? labelParts.slice(0, -1).join('.') : undefined
  return {
    id,
    name,
    namespace,
    schema_name: namespace,
    branch: undefined,
    format: undefined,
    asset_id: undefined,
    metadata: {},
  }
}

function isActive(pathname: string, href: string): boolean {
  const cleanPathname = cleanPath(pathname)
  const cleanHref = cleanPath(href)
  if (cleanHref === '/') return cleanPathname === '/'
  return (
    cleanPathname === cleanHref || cleanPathname.startsWith(`${cleanHref}/`)
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

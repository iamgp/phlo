import { Link, useRouterState } from '@tanstack/react-router'
import {
  Activity,
  Boxes,
  Database,
  GitBranch,
  LayoutDashboard,
  ListChecks,
  Logs,
  Plug,
  Search,
  Server,
  Settings,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type { V2ResourceResult, V2SearchResult } from '@/v2/api/types'
import { searchV2 } from '@/v2/api/resources'

const navItems = [
  { label: 'Overview', href: '/v2', icon: LayoutDashboard },
  { label: 'Services', href: '/v2/services', icon: Server },
  { label: 'Operations', href: '/v2/operations', icon: Activity },
  { label: 'Data', href: '/v2/data', icon: Database },
  { label: 'Assets', href: '/v2/assets', icon: Boxes },
  { label: 'Quality', href: '/v2/quality', icon: ListChecks },
  { label: 'Logs', href: '/v2/logs', icon: Logs },
  { label: 'Branches', href: '/v2/branches', icon: GitBranch },
  { label: 'Extensions', href: '/v2/extensions', icon: Plug },
  { label: 'Settings', href: '/v2/settings', icon: Settings },
]

export function V2Shell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })
  const [searchOpen, setSearchOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<
    V2ResourceResult<Array<V2SearchResult>>
  >({
    data: null,
    error: null,
  })

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
    <main className="phlo-v2">
      <div className="phlo-v2-shell">
        <nav className="phlo-v2-nav" aria-label="Observatory v2">
          <div className="phlo-v2-brand">
            <span className="phlo-v2-mark">P</span>
            <span>Phlo Observatory</span>
          </div>
          <div className="phlo-v2-nav-links">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.label}
                  to={item.href}
                  className="phlo-v2-nav-link"
                  data-active={isActive(pathname, item.href)}
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
          </div>
        </nav>
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
        <section className="phlo-v2-sheet">{children}</section>
      </div>
    </main>
  )
}

function isActive(pathname: string, href: string): boolean {
  if (href === '/v2') return pathname === '/v2'
  return pathname === href || pathname.startsWith(`${href}/`)
}

/**
 * Data Explorer Layout Route
 *
 * This layout route handles the shared sidebar with table browser.
 * Tables are loaded once here and passed to child routes via context.
 */
import { Outlet, createFileRoute, useNavigate } from '@tanstack/react-router'
import {
  ChevronDown,
  ChevronRight,
  Database,
  Folder,
  Search,
} from 'lucide-react'
import { useState } from 'react'

import type { IcebergTable } from '@/server/iceberg.server'
import { BranchSelector } from '@/components/data/BranchSelector'
import { Input } from '@/components/ui/input'
import { getTables } from '@/server/iceberg.server'

export const Route = createFileRoute('/data/$branchName')({
  loader: async ({ params }) => {
    const branch = decodeURIComponent(params.branchName)
    const tables = await getTables({ data: { branch } })
    return { tables }
  },
  component: DataExplorerLayout,
})

function DataExplorerLayout() {
  const navigate = useNavigate()
  const { branchName } = Route.useParams()
  const { tables } = Route.useLoaderData()
  const decodedBranchName = decodeURIComponent(branchName)

  const hasError = 'error' in tables
  const tableList = hasError ? [] : tables

  // Navigate to URL-based route when table is selected
  const handleTableSelect = (table: IcebergTable) => {
    navigate({
      to: '/data/$branchName/$schema/$table',
      params: {
        branchName,
        schema: table.schema,
        table: table.name,
      },
    })
  }

  return (
    <div className="flex h-full">
      {/* Left sidebar - Table Browser */}
      <aside className="w-72 border-r border-border bg-sidebar text-sidebar-foreground flex flex-col">
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="w-5 h-5 text-sidebar-primary" />
                Tables
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Browsing branch:{' '}
                <code className="bg-muted px-1 rounded-none">
                  {decodedBranchName}
                </code>
              </p>
            </div>
            <BranchSelector
              branch={decodedBranchName}
              onChange={(nextBranch) => {
                navigate({
                  to: '/data/$branchName',
                  params: { branchName: encodeURIComponent(nextBranch) },
                })
              }}
            />
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <TableBrowserCached
            tables={tableList}
            error={hasError ? (tables as { error: string }).error : null}
            onSelectTable={handleTableSelect}
          />
        </div>
      </aside>

      {/* Main content area - rendered by child route */}
      <Outlet />
    </div>
  )
}

/**
 * Cached version of TableBrowser that receives tables as props
 * instead of fetching them internally.
 */
interface TableBrowserCachedProps {
  tables: Array<IcebergTable>
  error: string | null
  onSelectTable: (table: IcebergTable) => void
}

function TableBrowserCached({
  tables,
  error,
  onSelectTable,
}: TableBrowserCachedProps) {
  const [search, setSearch] = useState('')
  const [expandedLayers, setExpandedLayers] = useState<Set<string>>(
    new Set(['bronze', 'silver', 'gold', 'publish']),
  )

  const toggleLayer = (layer: string) => {
    setExpandedLayers((prev) => {
      const next = new Set(prev)
      if (next.has(layer)) {
        next.delete(layer)
      } else {
        next.add(layer)
      }
      return next
    })
  }

  // Filter by search
  const filteredTables = tables.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()),
  )

  // Group by layer
  const tablesByLayer = filteredTables.reduce(
    (acc, table) => {
      if (!acc[table.layer]) acc[table.layer] = []
      acc[table.layer].push(table)
      return acc
    },
    {} as Record<string, Array<IcebergTable>>,
  )

  const layers: Array<{
    key: IcebergTable['layer']
    label: string
    color: string
  }> = [
    { key: 'bronze', label: 'Bronze (Raw)', color: 'text-amber-400' },
    { key: 'silver', label: 'Silver (Staged)', color: 'text-muted-foreground' },
    { key: 'gold', label: 'Gold (Curated)', color: 'text-primary' },
    { key: 'publish', label: 'Publish (Marts)', color: 'text-emerald-400' },
    { key: 'unknown', label: 'Other', color: 'text-muted-foreground' },
  ]

  if (error) {
    return (
      <div className="p-4 text-red-400 text-sm">
        <p className="font-medium mb-1">Failed to load tables</p>
        <p className="text-red-400/70">{error}</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tables..."
            className="pl-9"
          />
        </div>
      </div>

      {/* Table tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {layers.map((layer) => {
          const layerTables = tablesByLayer[layer.key] || []
          if (layerTables.length === 0) return null

          const isExpanded = expandedLayers.has(layer.key)

          return (
            <div key={layer.key} className="mb-2">
              <button
                onClick={() => toggleLayer(layer.key)}
                className="flex items-center gap-2 w-full px-2 py-1.5 hover:bg-muted/50 text-sm"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
                <Folder className={`w-4 h-4 ${layer.color}`} />
                <span className={layer.color}>{layer.label}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {layerTables.length}
                </span>
              </button>

              {isExpanded && (
                <div className="ml-6 mt-1 space-y-0.5">
                  {layerTables.map((table) => (
                    <button
                      key={table.name}
                      onClick={() => onSelectTable(table)}
                      className="flex items-center gap-2 w-full px-2 py-1.5 rounded text-sm transition-colors hover:bg-muted/50 text-muted-foreground hover:text-foreground"
                    >
                      <Database className="w-4 h-4 text-muted-foreground" />
                      <span className="truncate">{table.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        {filteredTables.length === 0 && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>{search ? 'No matching tables' : 'No tables found'}</p>
          </div>
        )}
      </div>
    </div>
  )
}

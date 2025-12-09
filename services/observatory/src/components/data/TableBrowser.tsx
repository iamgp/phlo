/**
 * Table Browser Component
 *
 * Tree view of Iceberg tables organized by layer.
 */

import {
  ChevronDown,
  ChevronRight,
  Database,
  Folder,
  Loader2,
  Search,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type {IcebergTable} from '@/server/iceberg.server';
import {  getTables } from '@/server/iceberg.server'

interface TableBrowserProps {
  branch: string
  selectedTable: string | null
  onSelectTable: (table: IcebergTable) => void
}

export function TableBrowser({
  branch,
  selectedTable,
  onSelectTable,
}: TableBrowserProps) {
  const [tables, setTables] = useState<Array<IcebergTable>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [expandedLayers, setExpandedLayers] = useState<Set<string>>(
    new Set(['bronze', 'silver', 'gold', 'publish']),
  )

  useEffect(() => {
    async function loadTables() {
      setLoading(true)
      setError(null)
      try {
        const result = await getTables({ data: { branch } })
        if ('error' in result) {
          setError(result.error)
        } else {
          setTables(result)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tables')
      } finally {
        setLoading(false)
      }
    }
    loadTables()
  }, [branch])

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

  const layers: Array<{ key: IcebergTable['layer']; label: string; color: string }> =
    [
      { key: 'bronze', label: 'Bronze (Raw)', color: 'text-amber-400' },
      { key: 'silver', label: 'Silver (Staged)', color: 'text-slate-300' },
      { key: 'gold', label: 'Gold (Curated)', color: 'text-yellow-400' },
      { key: 'publish', label: 'Publish (Marts)', color: 'text-green-400' },
      { key: 'unknown', label: 'Other', color: 'text-slate-500' },
    ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
      </div>
    )
  }

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
      <div className="p-3 border-b border-slate-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tables..."
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500"
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
                className="flex items-center gap-2 w-full px-2 py-1.5 hover:bg-slate-800 rounded text-sm"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                )}
                <Folder className={`w-4 h-4 ${layer.color}`} />
                <span className={layer.color}>{layer.label}</span>
                <span className="ml-auto text-xs text-slate-500">
                  {layerTables.length}
                </span>
              </button>

              {isExpanded && (
                <div className="ml-6 mt-1 space-y-0.5">
                  {layerTables.map((table) => (
                    <button
                      key={table.name}
                      onClick={() => onSelectTable(table)}
                      className={`flex items-center gap-2 w-full px-2 py-1.5 rounded text-sm transition-colors ${
                        selectedTable === table.name
                          ? 'bg-cyan-900/50 text-cyan-300'
                          : 'hover:bg-slate-800 text-slate-300'
                      }`}
                    >
                      <Database className="w-4 h-4 text-slate-500" />
                      <span className="truncate">{table.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        {filteredTables.length === 0 && (
          <div className="text-center py-8 text-slate-500 text-sm">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>{search ? 'No matching tables' : 'No tables found'}</p>
          </div>
        )}
      </div>
    </div>
  )
}

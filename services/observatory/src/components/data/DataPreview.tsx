import { ChevronLeft, ChevronRight, Loader2, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'
import { previewData } from '@/server/trino.server'

interface DataPreviewProps {
  table: string
  branch?: string
  initialData?: DataPreviewResult
  onShowJourney?: (
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => void
}

export function DataPreview({
  table,
  branch = 'main',
  onShowJourney,
}: DataPreviewProps) {
  const [data, setData] = useState<DataPreviewResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const pageSize = 50

  // Auto-load data when table changes (phlo-2m5 + phlo-bcr)
  useEffect(() => {
    // Reset state and load new data when table changes
    setData(null)
    setError(null)
    setPage(0)
    loadData(0)
  }, [table, branch])

  const loadData = async (offset = 0) => {
    setLoading(true)
    setError(null)
    try {
      const result = await previewData({
        data: { table, branch, limit: pageSize, offset },
      })
      if ('error' in result) {
        setError(result.error)
      } else {
        setData(result)
        setPage(Math.floor(offset / pageSize))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handlePrevPage = () => {
    if (page > 0) {
      loadData((page - 1) * pageSize)
    }
  }

  const handleNextPage = () => {
    if (data?.hasMore) {
      loadData((page + 1) * pageSize)
    }
  }

  const handleRowClick = (row: DataRow) => {
    if (onShowJourney && data) {
      onShowJourney(row, data.columnTypes)
    }
  }

  // Initial loading state (auto-loading in progress)
  if (!data && !loading && !error) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center">
        <Loader2 className="w-8 h-8 text-cyan-400 mx-auto mb-4 animate-spin" />
        <p className="text-slate-400">Loading preview...</p>
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center">
        <Loader2 className="w-8 h-8 text-cyan-400 mx-auto mb-4 animate-spin" />
        <p className="text-slate-400">Querying Trino...</p>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl border border-red-700/50 p-6">
        <div className="text-red-400 mb-4">{error}</div>
        <button
          onClick={() => loadData(page * pageSize)}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="font-medium">Data Preview</h3>
          <span className="text-xs text-slate-400 bg-slate-700 px-2 py-0.5 rounded">
            {data.rows.length} rows
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => loadData(page * pageSize)}
            className="p-2 hover:bg-slate-700 rounded transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-900/50">
              {data.columns.map((col, idx) => (
                <th
                  key={col}
                  className="text-left py-2 px-3 font-medium text-slate-400 whitespace-nowrap"
                >
                  <div className="flex flex-col gap-0.5">
                    <span>{col}</span>
                    <span className="text-xs font-normal text-slate-500">
                      {data.columnTypes[idx]}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                onClick={() => handleRowClick(row)}
                className={`border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors ${
                  onShowJourney ? 'cursor-pointer' : ''
                }`}
              >
                {data.columns.map((col) => (
                  <td
                    key={col}
                    className="py-2 px-3 whitespace-nowrap max-w-xs truncate"
                    title={String(row[col] ?? '')}
                  >
                    {formatCellValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="p-4 border-t border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-400">Page {page + 1}</div>
          {onShowJourney && (
            <div className="text-xs text-slate-500">
              Click any row to view lineage
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            disabled={page === 0}
            className="p-2 hover:bg-slate-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextPage}
            disabled={!data.hasMore}
            className="p-2 hover:bg-slate-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

// Format cell value for display
function formatCellValue(value: DataRow[keyof DataRow]): string {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }
  if (typeof value === 'number') {
    if (Number.isInteger(value)) {
      return value.toLocaleString()
    }
    return value.toFixed(4)
  }
  return String(value)
}

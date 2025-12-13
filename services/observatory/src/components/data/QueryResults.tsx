/**
 * Query Results Component
 *
 * Displays query results in a paginated table.
 */

import { ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { useState } from 'react'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'

interface QueryResultsProps {
  results: DataPreviewResult
  onShowJourney?: (
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => void
}

export function QueryResults({ results, onShowJourney }: QueryResultsProps) {
  const [page, setPage] = useState(0)
  const pageSize = 25
  const totalPages = Math.ceil(results.rows.length / pageSize)

  const paginatedRows = results.rows.slice(
    page * pageSize,
    (page + 1) * pageSize,
  )

  const handleRowClick = (row: DataRow) => {
    if (onShowJourney) {
      onShowJourney(row, results.columnTypes)
    }
  }

  const downloadCSV = () => {
    const header = results.columns.join(',')
    const rows = results.rows.map((row) =>
      results.columns
        .map((col) => {
          const val = row[col]
          if (val === null || val === undefined) return ''
          if (typeof val === 'string' && val.includes(',')) {
            return `"${val.replace(/"/g, '""')}"`
          }
          return String(val)
        })
        .join(','),
    )
    const csv = [header, ...rows].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query_results.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700">
        <div className="text-sm text-slate-400">
          {results.rows.length} row{results.rows.length !== 1 ? 's' : ''}
          {results.hasMore && '+'} • {results.columns.length} columns
        </div>
        <button
          onClick={downloadCSV}
          className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
        >
          <Download className="w-3 h-3" />
          CSV
        </button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-900">
            <tr className="border-b border-slate-700">
              {results.columns.map((col, idx) => (
                <th
                  key={col}
                  className="text-left py-2 px-3 font-medium text-slate-400 whitespace-nowrap"
                >
                  <div className="flex flex-col gap-0.5">
                    <span>{col}</span>
                    <span className="text-xs font-normal text-slate-500">
                      {results.columnTypes[idx]}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, rowIdx) => (
              <tr
                key={page * pageSize + rowIdx}
                onClick={() => handleRowClick(row)}
                className={`border-b border-slate-700/50 hover:bg-slate-800/50 transition-colors ${
                  onShowJourney ? 'cursor-pointer' : ''
                }`}
              >
                {results.columns.map((col) => (
                  <td
                    key={col}
                    className="py-2 px-3 whitespace-nowrap max-w-xs truncate font-mono text-xs"
                    title={String(row[col] ?? '')}
                  >
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between p-3 border-t border-slate-700">
          <div className="flex items-center gap-3">
            <div className="text-sm text-slate-500">
              Page {page + 1} of {totalPages}
            </div>
            {onShowJourney && (
              <div className="text-xs text-slate-500">
                Click any row to view lineage
              </div>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 hover:bg-slate-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 hover:bg-slate-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function formatValue(value: DataRow[keyof DataRow]): string {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  return String(value)
}

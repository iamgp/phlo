/**
 * Query Results Component
 *
 * Displays query results in a paginated table.
 */

import { ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { useState } from 'react'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

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
      <div className="flex items-center justify-between p-3 border-b">
        <div className="text-sm text-muted-foreground">
          {results.rows.length} row{results.rows.length !== 1 ? 's' : ''}
          {results.hasMore && '+'} • {results.columns.length} columns
        </div>
        <Button variant="outline" size="xs" onClick={downloadCSV}>
          <Download className="w-3 h-3" />
          CSV
        </Button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-card z-10">
            <TableRow>
              {results.columns.map((col, idx) => (
                <TableHead key={col} className="whitespace-nowrap">
                  <div className="flex flex-col gap-0.5">
                    <span>{col}</span>
                    <span className="text-xs font-normal text-muted-foreground">
                      {results.columnTypes[idx]}
                    </span>
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedRows.map((row, rowIdx) => (
              <TableRow
                key={page * pageSize + rowIdx}
                onClick={() => handleRowClick(row)}
                className={`transition-colors ${
                  onShowJourney ? 'cursor-pointer' : ''
                }`}
              >
                {results.columns.map((col) => (
                  <TableCell
                    key={col}
                    className="py-2 px-3 whitespace-nowrap max-w-xs truncate font-mono text-xs"
                    title={String(row[col] ?? '')}
                  >
                    {formatValue(row[col])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between p-3 border-t">
          <div className="flex items-center gap-3">
            <div className="text-sm text-muted-foreground">
              Page {page + 1} of {totalPages}
            </div>
            {onShowJourney && (
              <div className="text-xs text-muted-foreground">
                Click any row to view lineage
              </div>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
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

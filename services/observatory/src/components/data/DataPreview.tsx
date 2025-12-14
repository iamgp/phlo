import { ChevronLeft, ChevronRight, Loader2, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
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

  // Auto-load data when table changes
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
      <Card>
        <CardContent className="p-8 text-center">
          <Loader2 className="w-8 h-8 text-primary mx-auto mb-4 animate-spin" />
          <p className="text-muted-foreground">Loading preview...</p>
        </CardContent>
      </Card>
    )
  }

  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Loader2 className="w-8 h-8 text-primary mx-auto mb-4 animate-spin" />
          <p className="text-muted-foreground">Querying Trino...</p>
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className="border-destructive/30 bg-destructive/10">
        <CardContent className="p-6">
          <div className="text-destructive mb-4">{error}</div>
          <Button onClick={() => loadData(page * pageSize)} variant="outline">
            <RefreshCw className="w-4 h-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  return (
    <Card>
      {/* Header */}
      <CardHeader className="py-4">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base flex items-center gap-2">
            Data Preview
            <Badge variant="secondary" className="text-muted-foreground">
              {data.rows.length} rows
            </Badge>
          </CardTitle>
          <Button
            onClick={() => loadData(page * pageSize)}
            variant="ghost"
            size="icon-sm"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>

      {/* Table */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-card">
            <TableRow>
              {data.columns.map((col, idx) => (
                <TableHead key={col} className="whitespace-nowrap">
                  <div className="flex flex-col gap-0.5">
                    <span>{col}</span>
                    <span className="text-xs font-normal text-muted-foreground">
                      {data.columnTypes[idx]}
                    </span>
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.map((row, rowIdx) => (
              <TableRow
                key={rowIdx}
                onClick={() => handleRowClick(row)}
                className={`transition-colors ${
                  onShowJourney ? 'cursor-pointer' : ''
                }`}
              >
                {data.columns.map((col) => (
                  <TableCell
                    key={col}
                    className="py-2 px-3 whitespace-nowrap max-w-xs truncate"
                    title={String(row[col] ?? '')}
                  >
                    {formatCellValue(row[col])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="p-4 border-t flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">Page {page + 1}</div>
          {onShowJourney && (
            <div className="text-xs text-muted-foreground">
              Click any row to view lineage
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={handlePrevPage}
            disabled={page === 0}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={handleNextPage}
            disabled={!data.hasMore}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
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

/**
 * Data Explorer - Row Detail Page
 *
 * Shows the data journey for a specific row identified by _phlo_row_id.
 * Enables direct linking to row-level data journeys.
 */
import { createFileRoute, Link, useParams } from '@tanstack/react-router'
import {
  AlertCircle,
  ArrowLeft,
  Database,
  GitBranch,
  Loader2,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import { RowJourney } from '@/components/data/RowJourney'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import type { DataPreviewResult } from '@/server/trino.server'
import { getRowById } from '@/server/trino.server'
import { quoteIdentifier } from '@/utils/sqlIdentifiers'

export const Route = createFileRoute('/data/$branchName/$schema/$table/$rowId')(
  {
    component: RowDetailPage,
  },
)

function RowDetailPage() {
  const { branchName, schema, table, rowId } = useParams({
    from: '/data/$branchName/$schema/$table/$rowId',
  })
  const decodedRowId = decodeURIComponent(rowId)
  const { settings } = useObservatorySettings()

  const [rowData, setRowData] = useState<DataPreviewResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Wait for settings to be loaded
    if (!settings?.defaults?.catalog) {
      return
    }

    async function loadRow() {
      setLoading(true)
      setError(null)
      try {
        const catalog = settings.defaults.catalog
        const fullName = `${quoteIdentifier(catalog)}.${quoteIdentifier(schema)}.${quoteIdentifier(table)}`

        const result = await getRowById({
          data: {
            table: fullName,
            rowId: decodedRowId,
            catalog,
            schema,
            trinoUrl: settings.connections.trinoUrl,
            timeoutMs: settings.query.timeoutMs,
          },
        })

        if ('error' in result) {
          setError(result.error)
          setRowData(null)
        } else {
          setRowData(result)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load row')
        setRowData(null)
      } finally {
        setLoading(false)
      }
    }

    void loadRow()
  }, [decodedRowId, schema, table, settings])

  // Handle "Query Source Data" from journey view - navigate to SQL tab
  const handleQuerySource = (query: string) => {
    window.location.href = `/data/${branchName}/${schema}/${table}?sql=${encodeURIComponent(query)}&tab=query`
  }

  if (loading) {
    return (
      <main className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin" />
          <p>Loading row data...</p>
        </div>
      </main>
    )
  }

  if (error || !rowData || rowData.rows.length === 0) {
    return (
      <main className="flex-1 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-5 h-5" />
              Row Not Found
            </CardTitle>
            <CardDescription>
              {error || 'The requested row could not be found.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="text-sm text-muted-foreground">
                <p>
                  <strong>Table:</strong> {schema}.{table}
                </p>
                <p>
                  <strong>Row ID:</strong>{' '}
                  <code className="bg-muted px-1 rounded text-xs">
                    {decodedRowId}
                  </code>
                </p>
              </div>
              <Link
                to="/data/$branchName/$schema/$table"
                params={{ branchName, schema, table }}
                className="inline-flex items-center justify-center w-full h-8 gap-1.5 px-2.5 text-xs font-medium rounded-none border border-border bg-background hover:bg-muted"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Table
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
    )
  }

  const row = rowData.rows[0]

  return (
    <main className="flex-1 flex flex-col overflow-hidden min-h-0">
      {/* Header */}
      <header className="px-4 py-2 border-b bg-card">
        <div className="flex items-center gap-3">
          <Link
            to="/data/$branchName/$schema/$table"
            params={{ branchName, schema, table }}
            className="inline-flex items-center justify-center size-7 rounded-none hover:bg-muted"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2 min-w-0">
            <GitBranch className="w-4 h-4 text-primary" />
            <h1 className="text-lg font-semibold">Row Journey</h1>
            <Badge variant="secondary" className="text-muted-foreground">
              {table}
            </Badge>
          </div>
          <div className="flex-1" />
          <code className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded max-w-xs truncate">
            {decodedRowId}
          </code>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        <RowJourney
          assetKey={table}
          rowData={row as Record<string, unknown>}
          columnTypes={rowData.columnTypes}
          onQuerySource={handleQuerySource}
        />

        {/* Row Data Panel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="size-4 text-primary" />
              Row Data
            </CardTitle>
            <CardDescription>
              Data from {schema}.{table}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Column</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(row).map(([key, value], idx) => (
                    <TableRow key={key}>
                      <TableCell className="font-mono text-primary text-xs">
                        {key}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-xs">
                        {rowData.columnTypes[idx]}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {value === null || value === undefined
                          ? '—'
                          : String(value)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}

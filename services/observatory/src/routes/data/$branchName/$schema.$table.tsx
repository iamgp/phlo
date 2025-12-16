/**
 * Data Explorer - Table Detail Page
 *
 * This is a child of the layout route that shows the selected table's
 * preview, SQL editor, and journey view.
 */
import {
  createFileRoute,
  Outlet,
  useMatch,
  useNavigate,
  useParams,
} from '@tanstack/react-router'
import {
  ChevronLeft,
  ChevronRight,
  Database,
  GitBranch,
  RefreshCw,
  Terminal,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { z } from 'zod'

import { ObservatoryTable } from '@/components/data/ObservatoryTable'
import { QueryEditor } from '@/components/data/QueryEditor'
import { QueryResults } from '@/components/data/QueryResults'
import { RowJourney } from '@/components/data/RowJourney'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import type { IcebergTable } from '@/server/iceberg.server'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'
import { previewData } from '@/server/trino.server'
import { quoteIdentifier } from '@/utils/sqlIdentifiers'

export const Route = createFileRoute('/data/$branchName/$schema/$table')({
  validateSearch: z.object({
    sql: z.string().optional(),
    tab: z.enum(['preview', 'query', 'journey']).optional(),
  }),
  component: DataExplorerWithTable,
})

type TabType = 'preview' | 'query' | 'journey'

interface JourneyContext {
  assetKey: string
  tableName: string
  triggeredBy: 'preview' | 'query'
  rowData: Record<string, unknown>
  columnTypes: Array<string>
}

function DataExplorerWithTable() {
  // All hooks must be called before any conditional returns (React rules of hooks)
  const { branchName, schema, table } = useParams({
    from: '/data/$branchName/$schema/$table',
  })
  const { sql: sqlFromSearch, tab: tabFromSearch } = Route.useSearch()
  const decodedBranchName = decodeURIComponent(branchName)
  const { settings } = useObservatorySettings()
  const navigate = useNavigate()

  const [queryResults, setQueryResults] = useState<DataPreviewResult | null>(
    null,
  )
  const [activeTab, setActiveTab] = useState<TabType>('preview')
  const [journeyContext, setJourneyContext] = useState<JourneyContext | null>(
    null,
  )
  const [pendingQuery, setPendingQuery] = useState<string | null>(null)
  const [preview, setPreview] = useState<DataPreviewResult | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [previewPage, setPreviewPage] = useState(0)
  const previewPageSize = 50

  // Check if child route (row detail) is active
  const childMatch = useMatch({
    from: '/data/$branchName/$schema/$table/$rowId',
    shouldThrow: false,
  })

  // Reset state when table changes (fixes sidebar navigation bug)
  useEffect(() => {
    setJourneyContext(null)
    setActiveTab('preview')
    setQueryResults(null)
    setPendingQuery(null)
    setPreview(null)
    setPreviewError(null)
    setPreviewPage(0)
  }, [schema, table])

  useEffect(() => {
    if (tabFromSearch) {
      setActiveTab(tabFromSearch)
    }
    if (sqlFromSearch) {
      setPendingQuery(sqlFromSearch)
      setActiveTab('query')
    }
  }, [sqlFromSearch, tabFromSearch])

  // Construct the selected table from URL params
  const catalog = settings.defaults.catalog
  const fullName =
    schema === decodedBranchName
      ? `${quoteIdentifier(catalog)}.${quoteIdentifier(decodedBranchName)}.${quoteIdentifier(table)}`
      : `${quoteIdentifier(catalog)}.${quoteIdentifier(schema)}.${quoteIdentifier(table)}`

  const selectedTable: IcebergTable = {
    catalog,
    schema: schema,
    name: table,
    fullName,
    layer: inferLayerFromSchema(schema),
  }

  const handleShowJourney = (
    _table: IcebergTable,
    triggeredBy: 'preview' | 'query',
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => {
    // If the row has a _phlo_row_id, navigate to the row URL for shareability
    const phloRowId = rowData._phlo_row_id
    if (typeof phloRowId === 'string' && phloRowId) {
      void navigate({
        to: '/data/$branchName/$schema/$table/$rowId',
        params: {
          branchName,
          schema,
          table,
          rowId: encodeURIComponent(phloRowId),
        },
      })
      return
    }

    // Fallback: show journey inline (for tables without _phlo_row_id)
    setJourneyContext({
      assetKey: selectedTable.name,
      tableName: selectedTable.name,
      triggeredBy,
      rowData,
      columnTypes,
    })
    setActiveTab('journey')
  }

  // Handle "Query Source Data" from journey view
  const handleQuerySource = (query: string) => {
    setPendingQuery(query)
    setActiveTab('query')
  }

  const selectedTableDisplayName = useMemo(() => {
    if (schema === decodedBranchName) return table
    return `${schema}.${table}`
  }, [decodedBranchName, schema, table])

  const loadPreview = useCallback(
    async (offset: number) => {
      setPreviewLoading(true)
      setPreviewError(null)
      try {
        const result = await previewData({
          data: {
            table: selectedTable.fullName,
            branch: decodedBranchName,
            limit: previewPageSize,
            offset,
            trinoUrl: settings.connections.trinoUrl,
            timeoutMs: settings.query.timeoutMs,
            maxLimit: settings.query.maxLimit,
          },
        })
        if ('error' in result) {
          setPreviewError(result.error)
          setPreview(null)
          return
        }
        setPreview(result)
        setPreviewPage(Math.floor(offset / previewPageSize))
      } catch (err) {
        setPreviewError(
          err instanceof Error ? err.message : 'Failed to load preview',
        )
        setPreview(null)
      } finally {
        setPreviewLoading(false)
      }
    },
    [
      decodedBranchName,
      previewPageSize,
      selectedTable.fullName,
      settings.connections.trinoUrl,
      settings.query.maxLimit,
      settings.query.timeoutMs,
    ],
  )

  useEffect(() => {
    if (activeTab !== 'preview') return
    void loadPreview(0)
  }, [activeTab, loadPreview])

  // Render child route (row detail) if active
  if (childMatch) {
    return <Outlet />
  }

  const previewCanPrev =
    activeTab === 'preview' && previewPage > 0 && !previewLoading
  const previewCanNext =
    activeTab === 'preview' &&
    !!preview?.hasMore &&
    !previewLoading &&
    !previewError

  const handlePreviewPrev = () => {
    if (!previewCanPrev) return
    void loadPreview((previewPage - 1) * previewPageSize)
  }

  const handlePreviewNext = () => {
    if (!previewCanNext) return
    void loadPreview((previewPage + 1) * previewPageSize)
  }

  const handlePreviewRefresh = () => {
    if (activeTab !== 'preview') return
    void loadPreview(previewPage * previewPageSize)
  }

  return (
    <main className="flex-1 flex flex-col overflow-hidden min-h-0">
      {/* Header */}
      <header className="px-4 py-2 border-b bg-card">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <h1 className="text-lg font-semibold truncate">{table}</h1>
            {activeTab === 'preview' ? (
              <Badge variant="secondary" className="text-muted-foreground">
                {previewPageSize} rows
              </Badge>
            ) : null}
            <span className="text-xs text-muted-foreground truncate">
              {selectedTableDisplayName}
            </span>
          </div>

          <div className="flex-1 flex justify-center">
            <Tabs
              value={activeTab}
              onValueChange={(value) => setActiveTab(value as TabType)}
              className="gap-0"
            >
              <TabsList>
                <TabsTrigger value="preview">
                  <Database className="w-4 h-4" />
                  Preview
                </TabsTrigger>
                <TabsTrigger value="query">
                  <Terminal className="w-4 h-4" />
                  SQL
                </TabsTrigger>
                <TabsTrigger value="journey">
                  <GitBranch className="w-4 h-4" />
                  Journey
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <div className="flex items-center gap-2">
            {activeTab === 'preview' ? (
              <>
                <Button
                  onClick={handlePreviewRefresh}
                  variant="ghost"
                  size="icon-sm"
                  disabled={previewLoading}
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={handlePreviewPrev}
                  disabled={!previewCanPrev}
                  title="Previous"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={handlePreviewNext}
                  disabled={!previewCanNext}
                  title="Next"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </>
            ) : null}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-hidden min-h-0">
        {activeTab === 'journey' ? (
          journeyContext ? (
            <div className="h-full overflow-auto p-4 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium">
                    Data Journey: {journeyContext.tableName}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Lineage visualization showing transformations, ingestions,
                    and quality checks
                  </p>
                </div>
                <Badge variant="outline" className="text-xs">
                  {journeyContext.assetKey}
                </Badge>
              </div>
              <RowJourney
                assetKey={journeyContext.assetKey}
                rowData={journeyContext.rowData}
                columnTypes={journeyContext.columnTypes}
                onQuerySource={handleQuerySource}
              />

              {/* Row Data Panel */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Database className="size-4 text-primary" />
                    Selected Row Data
                  </CardTitle>
                  <CardDescription>
                    Data from {journeyContext.tableName}
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
                        {Object.entries(journeyContext.rowData).map(
                          ([key, value], idx) => (
                            <TableRow key={key}>
                              <TableCell className="font-mono text-primary text-xs">
                                {key}
                              </TableCell>
                              <TableCell className="text-muted-foreground text-xs">
                                {journeyContext.columnTypes[idx]}
                              </TableCell>
                              <TableCell className="font-mono text-xs">
                                {value === null || value === undefined
                                  ? '—'
                                  : String(value)}
                              </TableCell>
                            </TableRow>
                          ),
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <GitBranch className="w-16 h-16 mb-4 opacity-30" />
              <h3 className="text-lg font-medium">No journey selected</h3>
              <p className="text-sm mt-1">
                Click on any data row in Preview or SQL Query to view its
                lineage
              </p>
            </div>
          )
        ) : activeTab === 'preview' ? (
          <div className="h-full flex flex-col min-h-0 overflow-hidden">
            {previewError ? (
              <div className="p-4 text-sm text-destructive">{previewError}</div>
            ) : null}
            <ObservatoryTable
              columns={preview?.columns ?? []}
              columnTypes={preview?.columnTypes}
              rows={preview?.rows ?? []}
              getRowId={(_, index) =>
                `${previewPage * previewPageSize}-${index}`
              }
              onRowClick={(row) =>
                handleShowJourney(
                  selectedTable,
                  'preview',
                  row as Record<string, unknown>,
                  preview?.columnTypes ?? [],
                )
              }
              containerClassName="h-full border-0"
              maxHeightClassName="h-full"
              enableSorting
              enableColumnResizing
              enableColumnPinning
              formatCellValue={(value) =>
                formatPreviewCellValue(value as DataRow[keyof DataRow])
              }
            />
          </div>
        ) : (
          <div className="h-full overflow-auto p-4 space-y-4">
            <QueryEditor
              branch={decodedBranchName}
              defaultQuery={
                pendingQuery ||
                `SELECT * FROM ${selectedTable.fullName} LIMIT 100`
              }
              onResults={setQueryResults}
              autoRun={!!pendingQuery}
            />
            {queryResults && (
              <Card className="overflow-hidden">
                <QueryResults
                  results={queryResults}
                  onShowJourney={(rowData, columnTypes) =>
                    handleShowJourney(
                      selectedTable,
                      'query',
                      rowData,
                      columnTypes,
                    )
                  }
                />
              </Card>
            )}
          </div>
        )}
      </div>
    </main>
  )
}

// Helper to infer layer from schema name
function inferLayerFromSchema(schema: string): IcebergTable['layer'] {
  const s = schema.toLowerCase()
  if (s === 'bronze' || s === 'raw') return 'bronze'
  if (s === 'silver' || s === 'staging' || s === 'stg') return 'silver'
  if (s === 'gold' || s === 'curated') return 'gold'
  if (s === 'publish' || s === 'marts' || s === 'mart') return 'publish'
  return 'unknown'
}

function formatPreviewCellValue(value: DataRow[keyof DataRow]): string {
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

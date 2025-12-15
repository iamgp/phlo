import { createFileRoute, useNavigate, useParams } from '@tanstack/react-router'
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

import type { IcebergTable } from '@/server/iceberg.server'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'
import { BranchSelector } from '@/components/data/BranchSelector'
import { ObservatoryTable } from '@/components/data/ObservatoryTable'
import { QueryEditor } from '@/components/data/QueryEditor'
import { QueryResults } from '@/components/data/QueryResults'
import { RowJourney } from '@/components/data/RowJourney'
import { TableBrowser } from '@/components/data/TableBrowser'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { previewData } from '@/server/trino.server'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

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
  const { branchName, schema, table } = useParams({
    from: '/data/$branchName/$schema/$table',
  })
  const navigate = useNavigate()
  const { sql: sqlFromSearch, tab: tabFromSearch } = Route.useSearch()
  const decodedBranchName = decodeURIComponent(branchName)

  const [queryResults, setQueryResults] = useState<DataPreviewResult | null>(
    null,
  )
  const [activeTab, setActiveTab] = useState<TabType>('preview')
  const [journeyContext, setJourneyContext] = useState<JourneyContext | null>(
    null,
  )
  // Pre-configured query from journey view
  const [pendingQuery, setPendingQuery] = useState<string | null>(null)
  const [preview, setPreview] = useState<DataPreviewResult | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [previewPage, setPreviewPage] = useState(0)
  const previewPageSize = 50

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
  const fullName =
    schema === decodedBranchName
      ? `iceberg."${decodedBranchName}"."${table}"`
      : `iceberg.${schema}.${table}`

  const selectedTable: IcebergTable = {
    catalog: 'iceberg',
    schema: schema,
    name: table,
    fullName,
    layer: inferLayerFromSchema(schema),
  }

  const handleTableSelect = (newTable: IcebergTable) => {
    // Navigate to the new table URL
    navigate({
      to: '/data/$branchName/$schema/$table',
      params: {
        branchName,
        schema: newTable.schema,
        table: newTable.name,
      },
    })
  }

  const handleShowJourney = (
    _table: IcebergTable,
    triggeredBy: 'preview' | 'query',
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => {
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
    [decodedBranchName, previewPageSize, selectedTable.fullName],
  )

  useEffect(() => {
    if (activeTab !== 'preview') return
    void loadPreview(0)
  }, [activeTab, loadPreview])

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
    <div className="flex h-full">
      {/* Left sidebar - Table Browser */}
      <aside className="w-72 border-r bg-sidebar text-sidebar-foreground flex flex-col">
        <div className="px-4 py-3 border-b">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="w-5 h-5 text-sidebar-primary" />
                Tables
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Branch:{' '}
                <code className="bg-muted px-1 rounded-none">
                  {decodedBranchName}
                </code>{' '}
                · Schema:{' '}
                <code className="bg-muted px-1 rounded-none">{schema}</code>
              </p>
            </div>
            <BranchSelector
              branch={decodedBranchName}
              onChange={(nextBranch) => {
                navigate({
                  to: '/data/$branchName/$schema/$table',
                  params: {
                    branchName: encodeURIComponent(nextBranch),
                    schema,
                    table,
                  },
                  search: (prev) => prev,
                })
              }}
            />
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <TableBrowser
            branch={decodedBranchName}
            selectedTable={selectedTable.name}
            onSelectTable={handleTableSelect}
          />
        </div>
      </aside>

      {/* Main content area */}
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
            <div className="h-full flex flex-col overflow-hidden min-h-0">
              {previewError ? (
                <div className="p-4 text-sm text-destructive">
                  {previewError}
                </div>
              ) : null}
              <div className="flex-1 overflow-hidden min-h-0">
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
                  containerClassName="h-full border-t-0"
                  maxHeightClassName="h-full min-h-0"
                  enableSorting
                  enableColumnResizing
                  enableColumnPinning
                  formatCellValue={(value) =>
                    formatPreviewCellValue(value as DataRow[keyof DataRow])
                  }
                />
              </div>
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
    </div>
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

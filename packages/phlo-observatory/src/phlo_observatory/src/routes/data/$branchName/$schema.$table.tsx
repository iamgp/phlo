/**
 * Data Explorer - Table Detail Page
 *
 * This is a child of the layout route that shows the selected table's
 * preview, SQL editor, and journey view.
 */
import {
  Outlet,
  createFileRoute,
  useMatch,
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
import { useCallback, useEffect, useMemo, useReducer } from 'react'
import { z } from 'zod'

import type { IcebergTable } from '@/server/iceberg.server'
import type { DataPreviewResult, DataRow } from '@/server/trino.server'
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
import { previewData } from '@/server/trino.server'
import { quoteIdentifier } from '@/utils/sqlIdentifiers'

function deferNavigation(runNavigation: () => void) {
  queueMicrotask(runNavigation)
}

function openDataExplorerUrl(path: string) {
  if (typeof window !== 'undefined') {
    window.location.assign(path)
  }
}

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

type ExplorerState = {
  queryResults: DataPreviewResult | null
  activeTab: TabType
  journeyContext: JourneyContext | null
  pendingQuery: string | null
  preview: DataPreviewResult | null
  previewLoading: boolean
  previewError: string | null
  previewPage: number
}

type ExplorerAction =
  | { type: 'resetForTable' }
  | { type: 'syncSearch'; sql?: string; tab?: TabType }
  | { type: 'setTab'; tab: TabType }
  | { type: 'setQueryResults'; results: DataPreviewResult | null }
  | { type: 'showJourney'; context: JourneyContext }
  | { type: 'querySource'; query: string }
  | { type: 'previewStart' }
  | { type: 'previewSuccess'; preview: DataPreviewResult; page: number }
  | { type: 'previewError'; error: string }

const initialExplorerState: ExplorerState = {
  queryResults: null,
  activeTab: 'preview',
  journeyContext: null,
  pendingQuery: null,
  preview: null,
  previewLoading: false,
  previewError: null,
  previewPage: 0,
}

function explorerReducer(
  state: ExplorerState,
  action: ExplorerAction,
): ExplorerState {
  switch (action.type) {
    case 'resetForTable':
      return initialExplorerState
    case 'syncSearch':
      return {
        ...state,
        activeTab: action.sql ? 'query' : (action.tab ?? 'preview'),
        pendingQuery: action.sql ?? null,
      }
    case 'setTab':
      return { ...state, activeTab: action.tab }
    case 'setQueryResults':
      return { ...state, queryResults: action.results }
    case 'showJourney':
      return {
        ...state,
        activeTab: 'journey',
        journeyContext: action.context,
      }
    case 'querySource':
      return {
        ...state,
        activeTab: 'query',
        pendingQuery: action.query,
      }
    case 'previewStart':
      return { ...state, previewLoading: true, previewError: null }
    case 'previewSuccess':
      return {
        ...state,
        preview: action.preview,
        previewError: null,
        previewLoading: false,
        previewPage: action.page,
      }
    case 'previewError':
      return {
        ...state,
        preview: null,
        previewError: action.error,
        previewLoading: false,
      }
  }
}

function DataExplorerWithTable() {
  // All hooks must be called before any conditional returns (React rules of hooks)
  const { branchName, schema, table } = useParams({
    from: '/data/$branchName/$schema/$table',
  })
  const { sql: sqlFromSearch, tab: tabFromSearch } = Route.useSearch()
  const decodedBranchName = decodeURIComponent(branchName)
  const { settings } = useObservatorySettings()
  const [state, dispatch] = useReducer(explorerReducer, initialExplorerState)
  const {
    activeTab,
    journeyContext,
    pendingQuery,
    preview,
    previewError,
    previewLoading,
    previewPage,
    queryResults,
  } = state
  const previewPageSize = 50

  // Check if child route (row detail) is active
  const childMatch = useMatch({
    from: '/data/$branchName/$schema/$table/$rowId',
    shouldThrow: false,
  })

  // Reset state when table changes (fixes sidebar navigation bug)
  useEffect(() => {
    dispatch({ type: 'resetForTable' })
  }, [branchName, schema, table])

  useEffect(() => {
    dispatch({ type: 'syncSearch', sql: sqlFromSearch, tab: tabFromSearch })
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
      deferNavigation(() => {
        openDataExplorerUrl(
          `/data/${branchName}/${schema}/${table}/${encodeURIComponent(
            phloRowId,
          )}`,
        )
      })
      return
    }

    // Fallback: show journey inline (for tables without _phlo_row_id)
    dispatch({
      type: 'showJourney',
      context: {
        assetKey: selectedTable.name,
        tableName: selectedTable.name,
        triggeredBy,
        rowData,
        columnTypes,
      },
    })
  }

  // Handle "Query Source Data" from journey view
  const handleQuerySource = (query: string) => {
    dispatch({ type: 'querySource', query })
  }

  const selectedTableDisplayName = useMemo(() => {
    if (schema === decodedBranchName) return table
    return `${schema}.${table}`
  }, [decodedBranchName, schema, table])

  const loadPreview = useCallback(
    async (offset: number) => {
      dispatch({ type: 'previewStart' })
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
          dispatch({ type: 'previewError', error: result.error })
          return
        }
        dispatch({
          type: 'previewSuccess',
          preview: result,
          page: Math.floor(offset / previewPageSize),
        })
      } catch (err) {
        dispatch({
          type: 'previewError',
          error: err instanceof Error ? err.message : 'Failed to load preview',
        })
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
      <DataExplorerHeader
        activeTab={activeTab}
        displayName={selectedTableDisplayName}
        previewCanNext={previewCanNext}
        previewCanPrev={previewCanPrev}
        previewLoading={previewLoading}
        previewPageSize={previewPageSize}
        table={table}
        onPreviewNext={handlePreviewNext}
        onPreviewPrev={handlePreviewPrev}
        onPreviewRefresh={handlePreviewRefresh}
        onTabChange={(tab) => dispatch({ type: 'setTab', tab })}
      />
      <DataExplorerContent
        activeTab={activeTab}
        branch={decodedBranchName}
        journeyContext={journeyContext}
        pendingQuery={pendingQuery}
        preview={preview}
        previewError={previewError}
        previewPage={previewPage}
        previewPageSize={previewPageSize}
        queryResults={queryResults}
        selectedTable={selectedTable}
        onQueryResults={(results) =>
          dispatch({ type: 'setQueryResults', results })
        }
        onQuerySource={handleQuerySource}
        onShowJourney={handleShowJourney}
      />
    </main>
  )
}

function DataExplorerHeader({
  activeTab,
  displayName,
  previewCanNext,
  previewCanPrev,
  previewLoading,
  previewPageSize,
  table,
  onPreviewNext,
  onPreviewPrev,
  onPreviewRefresh,
  onTabChange,
}: {
  activeTab: TabType
  displayName: string
  previewCanNext: boolean
  previewCanPrev: boolean
  previewLoading: boolean
  previewPageSize: number
  table: string
  onPreviewNext: () => void
  onPreviewPrev: () => void
  onPreviewRefresh: () => void
  onTabChange: (tab: TabType) => void
}) {
  return (
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
            {displayName}
          </span>
        </div>
        <div className="flex-1 flex justify-center">
          <Tabs
            value={activeTab}
            onValueChange={(value) => onTabChange(value as TabType)}
            className="gap-0"
          >
            <TabsList>
              <TabsTrigger value="preview">
                <Database className="size-4" />
                Preview
              </TabsTrigger>
              <TabsTrigger value="query">
                <Terminal className="size-4" />
                SQL
              </TabsTrigger>
              <TabsTrigger value="journey">
                <GitBranch className="size-4" />
                Journey
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        <PreviewPager
          active={activeTab === 'preview'}
          disabled={previewLoading}
          canNext={previewCanNext}
          canPrev={previewCanPrev}
          onNext={onPreviewNext}
          onPrev={onPreviewPrev}
          onRefresh={onPreviewRefresh}
        />
      </div>
    </header>
  )
}

function PreviewPager({
  active,
  canNext,
  canPrev,
  disabled,
  onNext,
  onPrev,
  onRefresh,
}: {
  active: boolean
  canNext: boolean
  canPrev: boolean
  disabled: boolean
  onNext: () => void
  onPrev: () => void
  onRefresh: () => void
}) {
  if (!active) return <div className="flex items-center gap-2" />
  return (
    <div className="flex items-center gap-2">
      <Button
        onClick={onRefresh}
        variant="ghost"
        size="icon-sm"
        disabled={disabled}
        title="Refresh"
      >
        <RefreshCw className="size-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onPrev}
        disabled={!canPrev}
        title="Previous"
      >
        <ChevronLeft className="size-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onNext}
        disabled={!canNext}
        title="Next"
      >
        <ChevronRight className="size-4" />
      </Button>
    </div>
  )
}

function DataExplorerContent({
  activeTab,
  branch,
  journeyContext,
  pendingQuery,
  preview,
  previewError,
  previewPage,
  previewPageSize,
  queryResults,
  selectedTable,
  onQueryResults,
  onQuerySource,
  onShowJourney,
}: {
  activeTab: TabType
  branch: string
  journeyContext: JourneyContext | null
  pendingQuery: string | null
  preview: DataPreviewResult | null
  previewError: string | null
  previewPage: number
  previewPageSize: number
  queryResults: DataPreviewResult | null
  selectedTable: IcebergTable
  onQueryResults: (results: DataPreviewResult | null) => void
  onQuerySource: (query: string) => void
  onShowJourney: (
    table: IcebergTable,
    triggeredBy: 'preview' | 'query',
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => void
}) {
  return (
    <div className="flex-1 overflow-hidden min-h-0">
      {activeTab === 'journey' ? (
        <JourneyTab context={journeyContext} onQuerySource={onQuerySource} />
      ) : activeTab === 'preview' ? (
        <PreviewTab
          preview={preview}
          previewError={previewError}
          previewPage={previewPage}
          previewPageSize={previewPageSize}
          selectedTable={selectedTable}
          onShowJourney={onShowJourney}
        />
      ) : (
        <QueryTab
          branch={branch}
          pendingQuery={pendingQuery}
          queryResults={queryResults}
          selectedTable={selectedTable}
          onQueryResults={onQueryResults}
          onShowJourney={onShowJourney}
        />
      )}
    </div>
  )
}

function JourneyTab({
  context,
  onQuerySource,
}: {
  context: JourneyContext | null
  onQuerySource: (query: string) => void
}) {
  if (!context) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
        <GitBranch className="size-16 mb-4 opacity-30" />
        <h3 className="text-lg font-medium">No journey selected</h3>
        <p className="text-sm mt-1">
          Click on any data row in Preview or SQL Query to view its lineage
        </p>
      </div>
    )
  }
  return (
    <div className="h-full overflow-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">
            Data Journey: {context.tableName}
          </h3>
          <p className="text-sm text-muted-foreground">
            Lineage visualization showing transformations, ingestions, and
            quality checks
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          {context.assetKey}
        </Badge>
      </div>
      <RowJourney
        assetKey={context.assetKey}
        rowData={context.rowData}
        columnTypes={context.columnTypes}
        onQuerySource={onQuerySource}
      />
      <JourneyRowData context={context} />
    </div>
  )
}

function JourneyRowData({ context }: { context: JourneyContext }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Database className="size-4 text-primary" />
          Selected Row Data
        </CardTitle>
        <CardDescription>Data from {context.tableName}</CardDescription>
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
              {Object.entries(context.rowData).map(([key, value], idx) => (
                <TableRow key={key}>
                  <TableCell className="font-mono text-primary text-xs">
                    {key}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs">
                    {context.columnTypes[idx]}
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
  )
}

function PreviewTab({
  preview,
  previewError,
  previewPage,
  previewPageSize,
  selectedTable,
  onShowJourney,
}: {
  preview: DataPreviewResult | null
  previewError: string | null
  previewPage: number
  previewPageSize: number
  selectedTable: IcebergTable
  onShowJourney: (
    table: IcebergTable,
    triggeredBy: 'preview',
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => void
}) {
  return (
    <div className="h-full flex flex-col min-h-0 overflow-hidden">
      {previewError ? (
        <div className="p-4 text-sm text-destructive">{previewError}</div>
      ) : null}
      <ObservatoryTable
        columns={preview?.columns ?? []}
        columnTypes={preview?.columnTypes}
        rows={preview?.rows ?? []}
        getRowId={(_, index) => `${previewPage * previewPageSize}-${index}`}
        onRowClick={(row) =>
          onShowJourney(
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
  )
}

function QueryTab({
  branch,
  pendingQuery,
  queryResults,
  selectedTable,
  onQueryResults,
  onShowJourney,
}: {
  branch: string
  pendingQuery: string | null
  queryResults: DataPreviewResult | null
  selectedTable: IcebergTable
  onQueryResults: (results: DataPreviewResult | null) => void
  onShowJourney: (
    table: IcebergTable,
    triggeredBy: 'query',
    rowData: Record<string, unknown>,
    columnTypes: Array<string>,
  ) => void
}) {
  return (
    <div className="h-full overflow-auto p-4 space-y-4">
      <QueryEditor
        key={`${selectedTable.fullName}:${pendingQuery ?? 'default'}`}
        branch={branch}
        defaultQuery={
          pendingQuery || `SELECT * FROM ${selectedTable.fullName} LIMIT 100`
        }
        onResults={onQueryResults}
        autoRun={!!pendingQuery}
      />
      {queryResults && (
        <Card className="overflow-hidden">
          <QueryResults
            results={queryResults}
            onShowJourney={(rowData, columnTypes) =>
              onShowJourney(selectedTable, 'query', rowData, columnTypes)
            }
          />
        </Card>
      )}
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

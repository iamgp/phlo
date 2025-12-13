import { createFileRoute, useNavigate, useParams } from '@tanstack/react-router'
import { Database, GitBranch, Terminal } from 'lucide-react'
import { useEffect, useState } from 'react'

import type { IcebergTable } from '@/server/iceberg.server'
import type { DataPreviewResult } from '@/server/trino.server'
import { DataPreview } from '@/components/data/DataPreview'
import { QueryEditor } from '@/components/data/QueryEditor'
import { QueryResults } from '@/components/data/QueryResults'
import { RowJourney } from '@/components/data/RowJourney'
import { TableBrowser } from '@/components/data/TableBrowser'

export const Route = createFileRoute('/data/$schema/$table')({
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
  const { schema, table } = useParams({ from: '/data/$schema/$table' })
  const navigate = useNavigate()

  const [queryResults, setQueryResults] = useState<DataPreviewResult | null>(
    null,
  )
  const [activeTab, setActiveTab] = useState<TabType>('preview')
  const [journeyContext, setJourneyContext] = useState<JourneyContext | null>(
    null,
  )
  // Pre-configured query from journey view (phlo-gxl)
  const [pendingQuery, setPendingQuery] = useState<string | null>(null)

  // Reset state when table changes (fixes sidebar navigation bug)
  useEffect(() => {
    setJourneyContext(null)
    setActiveTab('preview')
    setQueryResults(null)
    setPendingQuery(null)
  }, [schema, table])

  // Construct the selected table from URL params
  const selectedTable: IcebergTable = {
    catalog: 'iceberg',
    schema: schema,
    name: table,
    fullName: `iceberg.${schema}.${table}`,
    layer: inferLayerFromSchema(schema),
  }

  const handleTableSelect = (newTable: IcebergTable) => {
    // Navigate to the new table URL
    navigate({
      to: '/data/$schema/$table',
      params: { schema: newTable.schema, table: newTable.name },
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

  // Handle "Query Source Data" from journey view (phlo-gxl)
  const handleQuerySource = (query: string) => {
    setPendingQuery(query)
    setActiveTab('query')
  }

  return (
    <div className="flex h-full">
      {/* Left sidebar - Table Browser */}
      <aside className="w-72 border-r border-slate-700 bg-slate-800/50 flex flex-col">
        <div className="h-[72px] p-4 border-b border-slate-700 flex flex-col justify-center">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            Tables
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Browsing schema:{' '}
            <code className="bg-slate-700 px-1 rounded">{schema}</code>
          </p>
        </div>
        <div className="flex-1 overflow-hidden">
          <TableBrowser
            branch="main"
            selectedTable={selectedTable.name}
            onSelectTable={handleTableSelect}
          />
        </div>
      </aside>

      {/* Main content area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-[72px] px-4 border-b border-slate-700 bg-slate-800/30 flex items-center justify-between">
          <div className="flex flex-col justify-center">
            <h1 className="text-lg font-semibold">{table}</h1>
            <p className="text-xs text-slate-400 mt-1">
              {schema}.{table} · Click rows to explore lineage
            </p>
          </div>
          {/* Tab switcher */}
          <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
                activeTab === 'preview'
                  ? 'bg-cyan-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Database className="w-4 h-4" />
              Preview
            </button>
            <button
              onClick={() => setActiveTab('query')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
                activeTab === 'query'
                  ? 'bg-cyan-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Terminal className="w-4 h-4" />
              SQL Query
            </button>
            <button
              onClick={() => setActiveTab('journey')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
                activeTab === 'journey'
                  ? 'bg-cyan-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitBranch className="w-4 h-4" />
              Journey
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'journey' ? (
            journeyContext ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-slate-200">
                      Data Journey: {journeyContext.tableName}
                    </h3>
                    <p className="text-sm text-slate-400">
                      Lineage visualization showing transformations, ingestions,
                      and quality checks
                    </p>
                  </div>
                  <div className="text-xs text-slate-500">
                    Asset key:{' '}
                    <code className="bg-slate-700 px-2 py-1 rounded">
                      {journeyContext.assetKey}
                    </code>
                  </div>
                </div>
                <RowJourney
                  assetKey={journeyContext.assetKey}
                  rowData={journeyContext.rowData}
                  columnTypes={journeyContext.columnTypes}
                  onQuerySource={handleQuerySource}
                />

                {/* Row Data Panel */}
                <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                  <div className="p-4 border-b border-slate-700">
                    <h4 className="font-medium text-slate-200 flex items-center gap-2">
                      <Database className="w-4 h-4 text-cyan-400" />
                      Selected Row Data
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">
                      Data from {journeyContext.tableName}
                    </p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-900/50">
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-2 px-3 font-medium text-slate-400">
                            Column
                          </th>
                          <th className="text-left py-2 px-3 font-medium text-slate-400">
                            Type
                          </th>
                          <th className="text-left py-2 px-3 font-medium text-slate-400">
                            Value
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(journeyContext.rowData).map(
                          ([key, value], idx) => (
                            <tr
                              key={key}
                              className="border-b border-slate-700/50 hover:bg-slate-700/30"
                            >
                              <td className="py-2 px-3 font-mono text-xs text-cyan-400">
                                {key}
                              </td>
                              <td className="py-2 px-3 text-xs text-slate-500">
                                {journeyContext.columnTypes[idx]}
                              </td>
                              <td className="py-2 px-3 font-mono text-xs">
                                {value === null || value === undefined
                                  ? '—'
                                  : String(value)}
                              </td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-500">
                <GitBranch className="w-16 h-16 mb-4 opacity-30" />
                <h3 className="text-lg font-medium text-slate-400">
                  No journey selected
                </h3>
                <p className="text-sm mt-1">
                  Click on any data row in Preview or SQL Query to view its
                  lineage
                </p>
              </div>
            )
          ) : activeTab === 'preview' ? (
            <DataPreview
              table={selectedTable.fullName}
              branch={selectedTable.schema}
              onShowJourney={(rowData, columnTypes) =>
                handleShowJourney(
                  selectedTable,
                  'preview',
                  rowData,
                  columnTypes,
                )
              }
            />
          ) : (
            <div className="space-y-4">
              <QueryEditor
                branch={selectedTable.schema}
                defaultQuery={
                  pendingQuery ||
                  `SELECT * FROM ${selectedTable.fullName} LIMIT 100`
                }
                onResults={setQueryResults}
                autoRun={!!pendingQuery}
              />
              {queryResults && (
                <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
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
                </div>
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

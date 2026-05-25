/**
 * Data Explorer Layout Route
 *
 * This layout route handles the shared sidebar with table browser.
 * Tables are loaded once here and passed to child routes via context.
 */
import { Await, Outlet, createFileRoute, defer } from '@tanstack/react-router'
import { Database } from 'lucide-react'
import { Suspense } from 'react'

import type { IcebergTable } from '@/server/iceberg.server'
import { BranchSelector } from '@/components/data/BranchSelector'
import { SavedQueriesPanel } from '@/components/data/SavedQueriesPanel'
import { TableBrowserVirtualized } from '@/components/data/TableBrowserVirtualized'
import { getTables } from '@/server/iceberg.server'

function deferNavigation(runNavigation: () => void) {
  queueMicrotask(runNavigation)
}

function openDataExplorerUrl(path: string) {
  if (typeof window !== 'undefined') {
    window.location.assign(path)
  }
}

export const Route = createFileRoute('/data/$branchName')({
  loader: ({ params }) => ({
    data: defer(loadTables(params.branchName)),
  }),
  component: DataExplorerLayout,
})

async function loadTables(branchName: string) {
  void decodeURIComponent(branchName)
  return getTables({ data: {} })
}

function DataExplorerLayout() {
  const { branchName } = Route.useParams()
  const { data } = Route.useLoaderData()
  const decodedBranchName = decodeURIComponent(branchName)

  // Navigate to URL-based route when table is selected
  const handleTableSelect = (selectedTable: IcebergTable) => {
    deferNavigation(() => {
      openDataExplorerUrl(
        `/data/${branchName}/${encodeURIComponent(
          selectedTable.schema,
        )}/${encodeURIComponent(selectedTable.name)}`,
      )
    })
  }

  // Handle running a saved query - navigate to SQL tab with the query
  const handleRunSavedQuery = (query: string, branch?: string) => {
    // Use the saved query's branch if specified, otherwise current branch
    const targetBranch = branch || branchName
    deferNavigation(() => {
      const search = new URLSearchParams({ sql: query, tab: 'query' })
      openDataExplorerUrl(`/data/${targetBranch}?${search.toString()}`)
    })
  }

  return (
    <div className="flex h-full">
      {/* Left sidebar - Table Browser */}
      <aside className="w-72 border-r border-border bg-sidebar text-sidebar-foreground flex flex-col">
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="size-5 text-sidebar-primary" />
                Tables
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Browsing branch:{' '}
                <code className="bg-muted px-1 rounded-none">
                  {decodedBranchName}
                </code>
              </p>
            </div>
            <BranchSelector
              branch={decodedBranchName}
              onChange={(nextBranch) => {
                openDataExplorerUrl(`/data/${encodeURIComponent(nextBranch)}`)
              }}
            />
          </div>
        </div>
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-hidden">
            <Suspense fallback={<LoadingState message="Loading tables…" />}>
              <Await promise={data}>
                {(tables) => {
                  const hasError = 'error' in tables
                  const tableList = hasError ? [] : tables
                  return (
                    <TableBrowserVirtualized
                      tables={tableList}
                      error={hasError ? tables.error : null}
                      onSelectTable={handleTableSelect}
                    />
                  )
                }}
              </Await>
            </Suspense>
          </div>
          {/* Saved Queries Panel */}
          <div className="border-t border-border p-2">
            <SavedQueriesPanel onRunQuery={handleRunSavedQuery} />
          </div>
        </div>
      </aside>

      {/* Main content area - rendered by child route */}
      <Outlet />
    </div>
  )
}

function LoadingState({ message }: { message: string }) {
  return (
    <div className="p-4 text-center text-muted-foreground text-sm">
      {message}
    </div>
  )
}

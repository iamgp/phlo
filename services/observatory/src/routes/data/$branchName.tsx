/**
 * Data Explorer Layout Route
 *
 * This layout route handles the shared sidebar with table browser.
 * Tables are loaded once here and passed to child routes via context.
 */
import { Outlet, createFileRoute, useNavigate } from '@tanstack/react-router'
import { Database } from 'lucide-react'

import type { IcebergTable } from '@/server/iceberg.server'
import { BranchSelector } from '@/components/data/BranchSelector'
import { TableBrowserVirtualized } from '@/components/data/TableBrowserVirtualized'
import { getTables } from '@/server/iceberg.server'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'

export const Route = createFileRoute('/data/$branchName')({
  loader: async ({ params }) => {
    const branch = decodeURIComponent(params.branchName)
    const settings = await getEffectiveObservatorySettings()
    const tables = await getTables({
      data: {
        branch,
        catalog: settings.defaults.catalog,
        preferredSchema: settings.defaults.schema,
        trinoUrl: settings.connections.trinoUrl,
        timeoutMs: settings.query.timeoutMs,
      },
    })
    return { tables }
  },
  component: DataExplorerLayout,
})

function DataExplorerLayout() {
  const navigate = useNavigate()
  const { branchName } = Route.useParams()
  const { tables } = Route.useLoaderData()
  const decodedBranchName = decodeURIComponent(branchName)

  const hasError = 'error' in tables
  const tableList = hasError ? [] : tables

  // Navigate to URL-based route when table is selected
  const handleTableSelect = (selectedTable: IcebergTable) => {
    navigate({
      to: '/data/$branchName/$schema/$table',
      params: {
        branchName,
        schema: selectedTable.schema,
        table: selectedTable.name,
      },
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
                <Database className="w-5 h-5 text-sidebar-primary" />
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
                navigate({
                  to: '/data/$branchName',
                  params: { branchName: encodeURIComponent(nextBranch) },
                })
              }}
            />
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <TableBrowserVirtualized
            tables={tableList}
            error={hasError ? (tables as { error: string }).error : null}
            onSelectTable={handleTableSelect}
          />
        </div>
      </aside>

      {/* Main content area - rendered by child route */}
      <Outlet />
    </div>
  )
}

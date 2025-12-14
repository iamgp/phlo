import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Database } from 'lucide-react'

import type { IcebergTable } from '@/server/iceberg.server'
import { BranchSelector } from '@/components/data/BranchSelector'
import { TableBrowser } from '@/components/data/TableBrowser'

export const Route = createFileRoute('/data/$branchName/')({
  component: DataExplorerLanding,
})

/**
 * Landing page for Data Explorer - shows table browser with no table selected.
 * Selecting a table navigates to /data/$branchName/$schema/$table for URL-driven state.
 */
function DataExplorerLanding() {
  const navigate = useNavigate()
  const { branchName } = Route.useParams()
  const decodedBranchName = decodeURIComponent(branchName)

  // Navigate to URL-based route when table is selected
  const handleTableSelect = (table: IcebergTable) => {
    navigate({
      to: '/data/$branchName/$schema/$table',
      params: {
        branchName,
        schema: table.schema,
        table: table.name,
      },
    })
  }

  return (
    <div className="flex h-full">
      {/* Left sidebar - Table Browser */}
      <aside className="w-72 border-r border-slate-700 bg-slate-800/50 flex flex-col">
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                Tables
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Browsing branch:{' '}
                <code className="bg-slate-700 px-1 rounded">
                  {decodedBranchName}
                </code>
              </p>
            </div>
            <BranchSelector
              branch={decodedBranchName}
              onChange={(nextBranch) => {
                navigate({
                  to: '/data/$branchName/',
                  params: { branchName: encodeURIComponent(nextBranch) },
                })
              }}
            />
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <TableBrowser
            branch={decodedBranchName}
            selectedTable={null}
            onSelectTable={handleTableSelect}
          />
        </div>
      </aside>

      {/* Main content area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="p-4 border-b border-slate-700 bg-slate-800/30">
          <div>
            <h1 className="text-xl font-bold">Data Explorer</h1>
            <p className="text-sm text-slate-400">
              Browse, query, and explore your Iceberg tables
            </p>
          </div>
        </header>

        {/* Content - placeholder when no table selected */}
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-slate-500">
            <Database className="w-16 h-16 mx-auto mb-4 opacity-30" />
            <h3 className="text-lg font-medium text-slate-400">
              No table selected
            </h3>
            <p className="text-sm mt-1">
              Select a table from the sidebar to preview its data
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

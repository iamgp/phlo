import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Database, Table } from 'lucide-react'

import type { IcebergTable } from '@/server/iceberg.server'
import { BranchSelector } from '@/components/data/BranchSelector'
import { TableBrowser } from '@/components/data/TableBrowser'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

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
        <header className="px-4 py-3 border-b border-border bg-card">
          <h1 className="text-xl font-bold">Data Explorer</h1>
          <p className="text-sm text-muted-foreground">
            Browse, query, and explore your Iceberg tables
          </p>
        </header>

        {/* Content - placeholder when no table selected */}
        <div className="flex-1 overflow-auto">
          <div className="mx-auto w-full max-w-2xl px-6 py-10">
            <Card size="sm" className="w-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Table className="size-4 text-primary" />
                  Select a table to start
                </CardTitle>
                <CardDescription>
                  Choose a table from the left to preview data, run SQL, and
                  explore lineage.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                <ul className="list-disc pl-5 space-y-1">
                  <li>Use the search box to filter tables.</li>
                  <li>Switch branches with the selector in the sidebar.</li>
                  <li>Click a row in Preview to open the Journey view.</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}

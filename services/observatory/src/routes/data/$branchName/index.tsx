import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Database } from 'lucide-react'

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
      <aside className="w-72 border-r bg-sidebar text-sidebar-foreground flex flex-col">
        <div className="p-4 border-b">
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
        <header className="p-4 border-b bg-card">
          <h1 className="text-xl font-bold">Data Explorer</h1>
          <p className="text-sm text-muted-foreground">
            Browse, query, and explore your Iceberg tables
          </p>
        </header>

        {/* Content - placeholder when no table selected */}
        <div className="flex-1 flex items-center justify-center">
          <Card size="sm" className="max-w-md">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Database className="size-4 text-primary" />
                No table selected
              </CardTitle>
              <CardDescription>
                Select a table from the sidebar to preview its data
              </CardDescription>
            </CardHeader>
            <CardContent />
          </Card>
        </div>
      </main>
    </div>
  )
}

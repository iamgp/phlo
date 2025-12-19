/**
 * Data Explorer Landing Page (no table selected)
 *
 * This is a child of the layout route that shows the welcome message.
 * Also supports running saved queries via URL params.
 */
import { createFileRoute } from '@tanstack/react-router'
import { Table } from 'lucide-react'
import { useState } from 'react'
import { z } from 'zod'

import type { DataPreviewResult } from '@/server/trino.server'
import { QueryEditor } from '@/components/data/QueryEditor'
import { QueryResults } from '@/components/data/QueryResults'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const Route = createFileRoute('/data/$branchName/')({
  validateSearch: z.object({
    sql: z.string().optional(),
    tab: z.enum(['welcome', 'query']).optional(),
  }),
  component: DataExplorerLanding,
})

function DataExplorerLanding() {
  const { branchName } = Route.useParams()
  const { sql: sqlFromSearch, tab: tabFromSearch } = Route.useSearch()
  const decodedBranchName = decodeURIComponent(branchName)
  const [queryResults, setQueryResults] = useState<DataPreviewResult | null>(
    null,
  )

  // Show SQL editor if we have a query in the URL
  const showQueryEditor = tabFromSearch === 'query' || !!sqlFromSearch

  if (showQueryEditor) {
    return (
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="px-4 py-3 border-b border-border bg-card">
          <h1 className="text-xl font-bold">SQL Query</h1>
          <p className="text-sm text-muted-foreground">
            Run queries on branch: {decodedBranchName}
          </p>
        </header>

        {/* SQL Editor Content */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          <QueryEditor
            branch={decodedBranchName}
            defaultQuery={sqlFromSearch || ''}
            onResults={setQueryResults}
            autoRun={!!sqlFromSearch}
          />
          {queryResults && (
            <Card className="overflow-hidden">
              <QueryResults results={queryResults} />
            </Card>
          )}
        </div>
      </main>
    )
  }

  return (
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
  )
}

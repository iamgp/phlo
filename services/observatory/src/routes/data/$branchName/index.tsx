/**
 * Data Explorer Landing Page (no table selected)
 *
 * This is a child of the layout route that shows the welcome message.
 */
import { createFileRoute } from '@tanstack/react-router'
import { Table } from 'lucide-react'

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

function DataExplorerLanding() {
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

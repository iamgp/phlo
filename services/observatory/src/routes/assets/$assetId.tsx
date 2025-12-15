import { Link, createFileRoute } from '@tanstack/react-router'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Columns2,
  Database,
  GitBranch,
  History,
  Info,
  Shield,
  Table as TableIcon,
} from 'lucide-react'
import { useState } from 'react'
import type { ReactNode } from 'react'
import type { AssetDetails } from '@/server/dagster.server'
import type { QualityCheck } from '@/server/quality.server'
import { DataPreview } from '@/components/data/DataPreview'
import { DataJourney } from '@/components/provenance/DataJourney'
import { MaterializationTimeline } from '@/components/provenance/MaterializationTimeline'
import { Badge } from '@/components/ui/badge'
import { buttonVariants } from '@/components/ui/button'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import { getAssetDetails } from '@/server/dagster.server'
import { getAssetChecks } from '@/server/quality.server'

export const Route = createFileRoute('/assets/$assetId')({
  loader: async ({ params }) => {
    const asset = await getAssetDetails({ data: params.assetId })

    // Fetch checks but don't fail the whole page if it errors
    let checks: Array<QualityCheck> | { error: string } = {
      error: 'Not loaded',
    }
    try {
      checks = await getAssetChecks({
        data: { assetKey: params.assetId.split('/') },
      })
    } catch {
      // Quality checks are optional, don't block page load
      checks = { error: 'Failed to load checks' }
    }

    return { asset, checks }
  },
  component: AssetDetailPage,
})

type Tab = 'overview' | 'journey' | 'data' | 'quality'

function AssetDetailPage() {
  const { asset, checks } = Route.useLoaderData()
  const params = Route.useParams()
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  const hasError = 'error' in asset
  const assetData = hasError ? null : asset
  const checksData = 'error' in checks ? [] : checks

  if (hasError) {
    return (
      <div className="h-full overflow-auto">
        <div className="mx-auto w-full max-w-6xl px-4 py-6">
          <Link
            to="/assets"
            className={cn(
              buttonVariants({ variant: 'ghost', size: 'sm' }),
              'gap-2 mb-6',
            )}
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Assets
          </Link>
          <div className="p-6 bg-destructive/10 border border-destructive/30">
            <h2 className="text-xl font-bold mb-2">Asset Not Found</h2>
            <p className="text-destructive">
              {(asset as { error: string }).error}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const tabs: Array<{ id: Tab; label: string; icon: ReactNode }> = [
    { id: 'overview', label: 'Overview', icon: <Info className="w-4 h-4" /> },
    {
      id: 'journey',
      label: 'Journey',
      icon: <GitBranch className="w-4 h-4" />,
    },
    { id: 'data', label: 'Data', icon: <Database className="w-4 h-4" /> },
    { id: 'quality', label: 'Quality', icon: <Shield className="w-4 h-4" /> },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        <Link
          to="/assets"
          className={cn(
            buttonVariants({ variant: 'ghost', size: 'sm' }),
            'gap-2 mb-6',
          )}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Assets
        </Link>

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-primary/10">
              <Database className="w-8 h-8 text-primary" />
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{params.assetId}</h1>
              {assetData?.description && (
                <p className="text-muted-foreground">{assetData.description}</p>
              )}
              <div className="flex items-center gap-4 mt-3">
                {assetData?.groupName && (
                  <Badge variant="secondary" className="text-muted-foreground">
                    {assetData.groupName}
                  </Badge>
                )}
                {assetData?.computeKind && (
                  <Badge variant="outline">{assetData.computeKind}</Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as Tab)}
        >
          <TabsList variant="line" className="mb-6">
            {tabs.map((tab) => (
              <TabsTrigger key={tab.id} value={tab.id}>
                {tab.icon}
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab assetData={assetData} />
          </TabsContent>
          <TabsContent value="journey">
            <JourneyTab assetKey={params.assetId} />
          </TabsContent>
          <TabsContent value="data">
            <DataTab assetKey={params.assetId} />
          </TabsContent>
          <TabsContent value="quality">
            <QualityTab checks={checksData} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

// Overview Tab (existing content)
function OverviewTab({ assetData }: { assetData: AssetDetails | null }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Info className="w-5 h-5 text-muted-foreground" />
            Metadata
          </h2>
          {assetData?.metadata && assetData.metadata.length > 0 ? (
            <div className="space-y-3">
              {assetData.metadata.map((entry, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <span className="text-muted-foreground text-sm min-w-[120px]">
                    {entry.key}
                  </span>
                  <span className="text-sm font-mono break-all">
                    {entry.value}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No metadata available</p>
          )}
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TableIcon className="w-5 h-5 text-muted-foreground" />
            Ops
          </h2>
          {assetData?.opNames && assetData.opNames.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {assetData.opNames.map((op, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 text-sm bg-muted text-foreground font-mono"
                >
                  {op}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No ops defined</p>
          )}
        </Card>

        {/* Columns Section */}
        <Card className="overflow-hidden">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Columns2 className="w-5 h-5 text-muted-foreground" />
              Columns
              {assetData?.columns && (
                <Badge variant="secondary" className="text-muted-foreground">
                  {assetData.columns.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {assetData?.columns && assetData.columns.length > 0 ? (
              <div className="overflow-x-auto border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assetData.columns.map((col, idx) => {
                      const deps = assetData.columnLineage?.[col.name]
                      return (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-xs text-primary">
                            {col.name}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {col.type}
                          </TableCell>
                          <TableCell>
                            {deps && deps.length > 0 ? (
                              <div className="flex flex-col gap-1">
                                {deps.map((dep, depIdx) => (
                                  <Link
                                    key={depIdx}
                                    to="/assets/$assetId"
                                    params={{ assetId: dep.assetKey.join('/') }}
                                    className="text-xs text-primary hover:underline"
                                  >
                                    {dep.assetKey[dep.assetKey.length - 1]}.
                                    {dep.columnName}
                                  </Link>
                                ))}
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-xs">
                                —
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {col.description || '—'}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <p className="text-muted-foreground">
                No column schema available
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-muted-foreground" />
              <div>
                <div className="text-sm text-muted-foreground">
                  Last Materialized
                </div>
                <div>
                  {assetData?.lastMaterialization
                    ? new Date(
                        Number(assetData.lastMaterialization.timestamp),
                      ).toLocaleString()
                    : 'Never'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-muted-foreground" />
              <div>
                <div className="text-sm text-muted-foreground">Partitioned</div>
                <div>{assetData?.partitionDefinition ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Journey Tab
function JourneyTab({ assetKey }: { assetKey: string }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-primary" />
            Data Lineage
          </CardTitle>
          <CardDescription>
            Shows where this data comes from and where it goes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataJourney assetKey={assetKey} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="w-5 h-5 text-primary" />
            Materialization History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <MaterializationTimeline assetKey={assetKey} limit={10} />
        </CardContent>
      </Card>
    </div>
  )
}

// Data Tab
function DataTab({ assetKey }: { assetKey: string }) {
  // Extract table name from asset key (last segment)
  const tableName = assetKey.split('/').pop() || assetKey

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-primary" />
          Data Preview
        </h2>
        <DataPreview table={tableName} />
      </section>
    </div>
  )
}

// Quality Tab
function QualityTab({ checks }: { checks: Array<QualityCheck> }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />
            Quality Checks
            {checks.length > 0 && (
              <Badge variant="secondary" className="text-muted-foreground ml-1">
                {checks.length}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {checks.length > 0 ? (
            <div className="space-y-3">
              {checks.map((check) => (
                <div key={check.name} className="p-3 border">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{check.name}</span>
                    <Badge
                      variant="outline"
                      className={
                        check.status === 'PASSED'
                          ? 'border-green-500/30 bg-green-500/10 text-green-400'
                          : check.status === 'FAILED'
                            ? 'border-destructive/30 bg-destructive/10 text-destructive'
                            : 'border-border bg-muted text-muted-foreground'
                      }
                    >
                      {check.status}
                    </Badge>
                  </div>
                  {check.description && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {check.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No quality checks configured</p>
              <p className="text-sm mt-1">
                Add{' '}
                <code className="bg-muted px-1 rounded-none">
                  @phlo.quality
                </code>{' '}
                decorators to enable checks
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

import {
  Await,
  Link,
  createFileRoute,
  defer,
  useNavigate,
} from '@tanstack/react-router'
import {
  Calendar,
  Clock,
  Columns2,
  Database,
  GitBranch,
  History,
  Info,
  Layers,
  Search,
  Shield,
  Table as TableIcon,
  Terminal,
} from 'lucide-react'
import { Suspense, useState } from 'react'
import type { Asset, AssetDetails } from '@/server/dagster.server'
import type { QualityCheck } from '@/server/quality.server'
import type { ReactNode } from 'react'
import { DataPreview } from '@/components/data/DataPreview'
import { LogViewer } from '@/components/data/LogViewer'
import { DataJourney } from '@/components/provenance/DataJourney'
import { MaterializationTimeline } from '@/components/provenance/MaterializationTimeline'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
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
import { cn } from '@/lib/utils'
import { getAssetDetails, getAssets } from '@/server/dagster.server'
import { getAssetChecks } from '@/server/quality.server'
import { formatDate, formatDateTime } from '@/utils/dateFormat'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'

export const Route = createFileRoute('/assets/$assetId')({
  loader: ({ params }) => ({ data: defer(loadAssetDetails(params.assetId)) }),
  component: AssetDetailPage,
})

async function loadAssetDetails(assetId: string): Promise<{
  assets: Array<Asset> | { error: string }
  asset: AssetDetails | { error: string }
  checks: Array<QualityCheck> | { error: string }
}> {
  const settings = await getEffectiveObservatorySettings()
  const dagsterUrl = settings.connections.dagsterGraphqlUrl
  const assetKey = assetId.split('/')
  const assets = await getAssets({ data: { dagsterUrl } })
  const asset = await getAssetDetails({ data: { assetKey, dagsterUrl } })

  let checks: Array<QualityCheck> | { error: string } = {
    error: 'Not loaded',
  }
  try {
    checks = await getAssetChecks({ data: { assetKey, dagsterUrl } })
  } catch {
    checks = { error: 'Failed to load checks' }
  }

  return { assets, asset, checks }
}

type Tab = 'overview' | 'journey' | 'data' | 'quality' | 'logs'

function AssetDetailPage() {
  const { data } = Route.useLoaderData()
  const params = Route.useParams()

  return (
    <Suspense fallback={<LoadingState message="Loading asset..." />}>
      <Await promise={data}>
        {(resolved) => <AssetDetailContent params={params} {...resolved} />}
      </Await>
    </Suspense>
  )
}

function AssetDetailContent({
  params,
  assets,
  asset,
  checks,
}: {
  params: { assetId: string }
  assets: Array<Asset> | { error: string }
  asset: AssetDetails | { error: string }
  checks: Array<QualityCheck> | { error: string }
}) {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [searchQuery, setSearchQuery] = useState('')

  const hasAssetsError = 'error' in assets
  const assetList = hasAssetsError ? [] : assets

  const hasError = 'error' in asset
  const assetData = hasError ? null : asset
  const checksData = 'error' in checks ? [] : checks

  // Group assets by group name
  const groupedAssets = assetList.reduce(
    (acc, a) => {
      const group = a.groupName || 'Ungrouped'
      if (!acc[group]) {
        acc[group] = []
      }
      acc[group].push(a)
      return acc
    },
    {} as Record<string, Array<Asset>>,
  )

  // Filter assets by search query
  const filteredGroups = Object.entries(groupedAssets).reduce(
    (acc, [group, groupAssets]) => {
      const filtered = groupAssets.filter((a) => {
        const query = searchQuery.toLowerCase()
        return (
          a.keyPath.toLowerCase().includes(query) ||
          a.description?.toLowerCase().includes(query) ||
          a.groupName?.toLowerCase().includes(query) ||
          a.computeKind?.toLowerCase().includes(query)
        )
      })
      if (filtered.length > 0) {
        acc[group] = filtered
      }
      return acc
    },
    {} as Record<string, Array<Asset>>,
  )

  const tabs: Array<{ id: Tab; label: string; icon: ReactNode }> = [
    { id: 'overview', label: 'Overview', icon: <Info className="w-4 h-4" /> },
    {
      id: 'journey',
      label: 'Journey',
      icon: <GitBranch className="w-4 h-4" />,
    },
    { id: 'data', label: 'Data', icon: <Database className="w-4 h-4" /> },
    { id: 'quality', label: 'Quality', icon: <Shield className="w-4 h-4" /> },
    { id: 'logs', label: 'Logs', icon: <Terminal className="w-4 h-4" /> },
  ]

  return (
    <div className="flex h-full">
      {/* Left sidebar - Asset Browser */}
      <aside className="w-72 border-r bg-sidebar text-sidebar-foreground flex flex-col">
        <div className="px-4 py-3 border-b">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="w-5 h-5 text-sidebar-primary" />
                Assets
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                {hasAssetsError
                  ? 'Error loading assets'
                  : `${assetList.length} registered assets`}
              </p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search assets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-8 text-sm"
            />
          </div>
        </div>

        {/* Asset List */}
        <div className="flex-1 overflow-auto">
          {Object.keys(filteredGroups).length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              {searchQuery ? 'No assets match your search' : 'No assets found'}
            </div>
          ) : (
            <div className="py-1">
              {Object.entries(filteredGroups)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([group, groupAssets]) => (
                  <div key={group}>
                    <div className="px-3 py-2 text-xs font-medium text-muted-foreground flex items-center gap-2">
                      <Layers className="size-3" />
                      {group}
                      <Badge
                        variant="secondary"
                        className="text-muted-foreground ml-auto text-[10px] px-1.5"
                      >
                        {groupAssets.length}
                      </Badge>
                    </div>
                    {groupAssets.map((a) => (
                      <AssetListItem
                        key={a.id}
                        asset={a}
                        isSelected={a.keyPath === params.assetId}
                        onClick={() =>
                          navigate({
                            to: '/assets/$assetId',
                            params: { assetId: a.keyPath },
                          })
                        }
                      />
                    ))}
                  </div>
                ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main content area */}
      <main className="flex-1 flex flex-col overflow-hidden min-h-0">
        {/* Header */}
        <header className="px-4 py-2 border-b bg-card">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <h1 className="text-lg font-semibold truncate">
                {params.assetId}
              </h1>
              {assetData?.groupName && (
                <Badge variant="secondary" className="text-muted-foreground">
                  {assetData.groupName}
                </Badge>
              )}
              {assetData?.computeKind && (
                <Badge variant="outline">{assetData.computeKind}</Badge>
              )}
            </div>

            <div className="flex-1 flex justify-center">
              <Tabs
                value={activeTab}
                onValueChange={(value) => setActiveTab(value as Tab)}
                className="gap-0"
              >
                <TabsList>
                  {tabs.map((tab) => (
                    <TabsTrigger key={tab.id} value={tab.id}>
                      {tab.icon}
                      {tab.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto min-h-0">
          {hasError ? (
            <div className="p-6">
              <div className="p-6 bg-destructive/10 border border-destructive/30">
                <h2 className="text-xl font-bold mb-2">Asset Not Found</h2>
                <p className="text-destructive">
                  {(asset as { error: string }).error}
                </p>
              </div>
            </div>
          ) : (
            <div className="p-4">
              {activeTab === 'overview' && (
                <OverviewTab assetData={assetData} />
              )}
              {activeTab === 'journey' && (
                <JourneyTab assetKey={params.assetId} />
              )}
              {activeTab === 'data' && <DataTab assetKey={params.assetId} />}
              {activeTab === 'quality' && <QualityTab checks={checksData} />}
              {activeTab === 'logs' && <LogsTab assetKey={params.assetId} />}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function LoadingState({ message }: { message: string }) {
  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            <Clock className="w-6 h-6 mx-auto mb-3 opacity-60" />
            {message}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function AssetListItem({
  asset,
  isSelected,
  onClick,
}: {
  asset: Asset
  isSelected: boolean
  onClick: () => void
}) {
  const { settings } = useObservatorySettings()
  const lastMaterialized = asset.lastMaterialization
    ? formatTimeAgo(
        new Date(Number(asset.lastMaterialization.timestamp)),
        settings.ui.dateFormat,
      )
    : null

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full px-3 py-2 text-left transition-colors',
        'flex items-center gap-2 min-w-0',
        isSelected
          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
          : 'hover:bg-sidebar-accent/50',
      )}
    >
      <Database className="size-4 text-sidebar-primary shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{asset.keyPath}</div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {asset.computeKind && (
            <span className="truncate">{asset.computeKind}</span>
          )}
          {lastMaterialized && (
            <>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Clock className="size-3" />
                {lastMaterialized}
              </span>
            </>
          )}
        </div>
      </div>
    </button>
  )
}

function formatTimeAgo(date: Date, mode: 'iso' | 'local'): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(date, mode)
}

// Overview Tab
function OverviewTab({ assetData }: { assetData: AssetDetails | null }) {
  const { settings } = useObservatorySettings()
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 space-y-4">
        {assetData?.description && (
          <Card>
            <CardContent className="pt-4">
              <p className="text-muted-foreground">{assetData.description}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Info className="w-4 h-4 text-muted-foreground" />
              Metadata
            </CardTitle>
          </CardHeader>
          <CardContent>
            {assetData?.metadata && assetData.metadata.length > 0 ? (
              <div className="space-y-2">
                {assetData.metadata.map((entry, idx) => (
                  <div key={idx} className="flex items-start gap-4 text-sm">
                    <span className="text-muted-foreground min-w-[120px]">
                      {entry.key}
                    </span>
                    <span className="font-mono break-all">{entry.value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                No metadata available
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <TableIcon className="w-4 h-4 text-muted-foreground" />
              Ops
            </CardTitle>
          </CardHeader>
          <CardContent>
            {assetData?.opNames && assetData.opNames.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {assetData.opNames.map((op, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 text-xs bg-muted text-foreground font-mono"
                  >
                    {op}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No ops defined</p>
            )}
          </CardContent>
        </Card>

        {/* Columns Section */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Columns2 className="w-4 h-4 text-muted-foreground" />
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
                          <TableCell className="text-muted-foreground text-sm">
                            {col.description || '—'}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                No column schema available
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
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
                <div className="text-sm">
                  {assetData?.lastMaterialization
                    ? formatDateTime(
                        new Date(
                          Number(assetData.lastMaterialization.timestamp),
                        ),
                        settings.ui.dateFormat,
                      )
                    : 'Never'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-muted-foreground" />
              <div>
                <div className="text-sm text-muted-foreground">Partitioned</div>
                <div className="text-sm">
                  {assetData?.partitionDefinition ? 'Yes' : 'No'}
                </div>
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
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-primary" />
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
          <CardTitle className="text-base flex items-center gap-2">
            <History className="w-4 h-4 text-primary" />
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
    <div className="space-y-4">
      <section>
        <h2 className="text-base font-semibold mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-primary" />
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
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
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
                  @phlo_quality
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

// Logs Tab
function LogsTab({ assetKey }: { assetKey: string }) {
  return (
    <div className="space-y-4">
      <LogViewer assetKey={assetKey} />
    </div>
  )
}

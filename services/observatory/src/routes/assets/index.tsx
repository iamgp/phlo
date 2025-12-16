import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { ArrowRight, Clock, Database, Layers, Search } from 'lucide-react'
import { useState } from 'react'
import type { Asset } from '@/server/dagster.server'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { getAssets } from '@/server/dagster.server'
import { getEffectiveObservatorySettings } from '@/utils/effectiveSettings'

export const Route = createFileRoute('/assets/')({
  loader: async () => {
    const settings = await getEffectiveObservatorySettings()
    const assets = await getAssets({
      data: { dagsterUrl: settings.connections.dagsterGraphqlUrl },
    })
    return { assets }
  },
  component: AssetsPage,
})

function AssetsPage() {
  const { assets } = Route.useLoaderData()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const hasError = 'error' in assets
  const assetList = hasError ? [] : assets

  // Group assets by group name
  const groupedAssets = assetList.reduce(
    (acc, asset) => {
      const group = asset.groupName || 'Ungrouped'
      if (!acc[group]) {
        acc[group] = []
      }
      acc[group].push(asset)
      return acc
    },
    {} as Record<string, Array<Asset>>,
  )

  // Filter assets by search query
  const filteredGroups = Object.entries(groupedAssets).reduce(
    (acc, [group, groupAssets]) => {
      const filtered = groupAssets.filter((asset) => {
        const query = searchQuery.toLowerCase()
        return (
          asset.keyPath.toLowerCase().includes(query) ||
          asset.description?.toLowerCase().includes(query) ||
          asset.groupName?.toLowerCase().includes(query) ||
          asset.computeKind?.toLowerCase().includes(query)
        )
      })
      if (filtered.length > 0) {
        acc[group] = filtered
      }
      return acc
    },
    {} as Record<string, Array<Asset>>,
  )

  const totalFiltered = Object.values(filteredGroups).flat().length

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
                {hasError
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

        {/* Error Banner */}
        {hasError && (
          <div className="p-3 bg-destructive/10 text-destructive text-sm border-b">
            {(assets as { error: string }).error}
          </div>
        )}

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
                    {groupAssets.map((asset) => (
                      <AssetListItem
                        key={asset.id}
                        asset={asset}
                        onClick={() =>
                          navigate({
                            to: '/assets/$assetId',
                            params: { assetId: asset.keyPath },
                          })
                        }
                      />
                    ))}
                  </div>
                ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-3 py-2 border-t text-xs text-muted-foreground">
          {searchQuery
            ? `${totalFiltered} of ${assetList.length} assets`
            : `${assetList.length} assets`}
        </div>
      </aside>

      {/* Main content area */}
      <main className="flex-1 flex flex-col overflow-hidden min-h-0">
        {/* Header */}
        <header className="px-4 py-2 border-b bg-card">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <h1 className="text-lg font-semibold truncate">Assets</h1>
              <Badge variant="secondary" className="text-muted-foreground">
                {assetList.length} total
              </Badge>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto min-h-0 flex items-center justify-center">
          <div className="text-center text-muted-foreground">
            <Database className="w-16 h-16 mx-auto mb-4 opacity-30" />
            <h3 className="text-lg font-medium">Select an asset</h3>
            <p className="text-sm mt-1">
              Choose an asset from the sidebar to view its details
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

function AssetListItem({
  asset,
  onClick,
}: {
  asset: Asset
  onClick: () => void
}) {
  const lastMaterialized = asset.lastMaterialization
    ? formatTimeAgo(new Date(Number(asset.lastMaterialization.timestamp)))
    : null

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full px-3 py-2 text-left hover:bg-sidebar-accent transition-colors',
        'flex items-center gap-2 min-w-0',
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
      <ArrowRight className="size-4 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100" />
    </button>
  )
}

function formatTimeAgo(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

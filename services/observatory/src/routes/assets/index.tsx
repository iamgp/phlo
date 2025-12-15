import { Link, createFileRoute } from '@tanstack/react-router'
import { ArrowRight, Clock, Database, Search } from 'lucide-react'
import { useState } from 'react'
import type { Asset } from '@/server/dagster.server'
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
import { getAssets } from '@/server/dagster.server'

export const Route = createFileRoute('/assets/')({
  loader: async () => {
    const assets = await getAssets()
    return { assets }
  },
  component: AssetsPage,
})

function AssetsPage() {
  const { assets } = Route.useLoaderData()
  const [searchQuery, setSearchQuery] = useState('')

  const hasError = 'error' in assets
  const assetList = hasError ? [] : assets

  // Filter assets by search query
  const filteredAssets = assetList.filter((asset) => {
    const query = searchQuery.toLowerCase()
    return (
      asset.keyPath.toLowerCase().includes(query) ||
      asset.description?.toLowerCase().includes(query) ||
      asset.groupName?.toLowerCase().includes(query) ||
      asset.computeKind?.toLowerCase().includes(query)
    )
  })

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto w-full max-w-6xl px-4 py-6">
        <Card>
          <CardHeader className="gap-1">
            <CardTitle className="text-3xl">Assets</CardTitle>
            <CardDescription>
              {hasError
                ? 'Error loading assets'
                : `${assetList.length} registered assets`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Error Banner */}
            {hasError && (
              <div className="p-4 bg-destructive/10 text-destructive border border-destructive/30">
                <p>{(assets as { error: string }).error}</p>
              </div>
            )}

            {/* Search */}
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search assets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Asset Table */}
            <div className="border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset</TableHead>
                    <TableHead>Group</TableHead>
                    <TableHead>Kind</TableHead>
                    <TableHead>Last Materialized</TableHead>
                    <TableHead className="w-[64px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAssets.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="text-center text-muted-foreground py-10"
                      >
                        {searchQuery
                          ? 'No assets match your search'
                          : 'No assets found'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAssets.map((asset) => (
                      <AssetRow key={asset.id} asset={asset} />
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function AssetRow({ asset }: { asset: Asset }) {
  const lastMaterialized = asset.lastMaterialization
    ? formatTimeAgo(new Date(Number(asset.lastMaterialization.timestamp)))
    : 'Never'

  return (
    <TableRow className="group">
      <TableCell>
        <Link
          to="/assets/$assetId"
          params={{ assetId: asset.keyPath }}
          className="block"
        >
          <div className="flex items-center gap-3 min-w-0">
            <Database className="size-4 text-primary shrink-0" />
            <div className="min-w-0">
              <div className="font-medium truncate">{asset.keyPath}</div>
              {asset.description && (
                <div className="text-sm text-muted-foreground truncate">
                  {asset.description}
                </div>
              )}
            </div>
          </div>
        </Link>
      </TableCell>
      <TableCell>
        {asset.groupName ? (
          <Badge variant="secondary" className="text-muted-foreground">
            {asset.groupName}
          </Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </TableCell>
      <TableCell>
        {asset.computeKind ? (
          <Badge variant="outline">{asset.computeKind}</Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Clock className="size-4" />
          <span className="text-sm">{lastMaterialized}</span>
        </div>
      </TableCell>
      <TableCell className="text-right">
        <ArrowRight className="size-4 text-muted-foreground group-hover:text-foreground transition-colors inline-block" />
      </TableCell>
    </TableRow>
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

import { Link, createFileRoute } from '@tanstack/react-router'
import { ArrowRight, Clock, Database, Search } from 'lucide-react'
import { useState } from 'react'
import type {Asset} from '@/server/dagster.server';
import {  getAssets } from '@/server/dagster.server'

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
  const assetList = hasError ? [] : (assets)

  // Filter assets by search query
  const filteredAssets = assetList.filter(asset => {
    const query = searchQuery.toLowerCase()
    return (
      asset.keyPath.toLowerCase().includes(query) ||
      asset.description?.toLowerCase().includes(query) ||
      asset.groupName?.toLowerCase().includes(query) ||
      asset.computeKind?.toLowerCase().includes(query)
    )
  })

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Assets</h1>
          <p className="text-slate-400">
            {hasError ? 'Error loading assets' : `${assetList.length} registered assets`}
          </p>
        </div>
      </div>

      {/* Error Banner */}
      {hasError && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-700/50 rounded-xl">
          <p className="text-red-300">{(assets as { error: string }).error}</p>
        </div>
      )}

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search assets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Asset List */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-slate-750 border-b border-slate-700 text-sm font-medium text-slate-400">
          <div className="col-span-5">Asset</div>
          <div className="col-span-2">Group</div>
          <div className="col-span-2">Kind</div>
          <div className="col-span-2">Last Materialized</div>
          <div className="col-span-1"></div>
        </div>

        {/* Table Body */}
        {filteredAssets.length === 0 ? (
          <div className="px-6 py-12 text-center text-slate-500">
            {searchQuery ? 'No assets match your search' : 'No assets found'}
          </div>
        ) : (
          <div className="divide-y divide-slate-700">
            {filteredAssets.map((asset) => (
              <AssetRow key={asset.id} asset={asset} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function AssetRow({ asset }: { asset: Asset }) {
  const lastMaterialized = asset.lastMaterialization
    ? formatTimeAgo(new Date(Number(asset.lastMaterialization.timestamp)))
    : 'Never'

  return (
    <Link
      to="/assets/$assetId"
      params={{ assetId: asset.keyPath }}
      className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-slate-700/50 transition-colors items-center group"
    >
      <div className="col-span-5">
        <div className="flex items-center gap-3">
          <Database className="w-5 h-5 text-cyan-400 flex-shrink-0" />
          <div className="min-w-0">
            <div className="font-medium text-slate-100 truncate">{asset.keyPath}</div>
            {asset.description && (
              <div className="text-sm text-slate-400 truncate">{asset.description}</div>
            )}
          </div>
        </div>
      </div>
      <div className="col-span-2">
        {asset.groupName ? (
          <span className="px-2 py-1 text-xs font-medium bg-slate-700 text-slate-300 rounded">
            {asset.groupName}
          </span>
        ) : (
          <span className="text-slate-500">—</span>
        )}
      </div>
      <div className="col-span-2">
        {asset.computeKind ? (
          <span className="px-2 py-1 text-xs font-medium bg-purple-900/50 text-purple-300 rounded">
            {asset.computeKind}
          </span>
        ) : (
          <span className="text-slate-500">—</span>
        )}
      </div>
      <div className="col-span-2 flex items-center gap-2 text-slate-400">
        <Clock className="w-4 h-4" />
        <span className="text-sm">{lastMaterialized}</span>
      </div>
      <div className="col-span-1 flex justify-end">
        <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
      </div>
    </Link>
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

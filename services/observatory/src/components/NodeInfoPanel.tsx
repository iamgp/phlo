/**
 * NodeInfoPanel Component
 *
 * Sidebar panel showing details of selected graph node.
 */

import { Link } from '@tanstack/react-router'
import { AlertTriangle, ArrowDownLeft, ArrowUpRight, ChevronDown, ChevronRight, Clock, Database, ExternalLink, GitBranch, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { GraphNode, ImpactedAsset } from '@/server/graph.server'
import { getAssetImpact } from '@/server/graph.server'

interface NodeInfoPanelProps {
  node: GraphNode | null
  onClose: () => void
  onFocusGraph: (keyPath: string) => void
}

export function NodeInfoPanel({ node, onClose, onFocusGraph }: NodeInfoPanelProps) {
  if (!node) return null

  const lastMaterialized = node.lastMaterialization
    ? formatTimeAgo(new Date(Number(node.lastMaterialization)))
    : 'Never'

  return (
    <div className="w-80 bg-slate-800 border-l border-slate-700 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <span className="font-medium text-slate-100">Asset Details</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-700 rounded transition-colors"
        >
          <X className="w-4 h-4 text-slate-400" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Name & Layer Badge */}
        <div>
          <h3 className="text-lg font-semibold text-slate-100 break-all">{node.label}</h3>
          <div className="text-sm text-slate-400 mt-1 break-all">{node.keyPath}</div>
          <div className="flex items-center gap-2 mt-2">
            <LayerBadge layer={node.layer} />
            {node.computeKind && (
              <span className="px-2 py-0.5 text-xs font-medium bg-purple-900/50 text-purple-300 rounded">
                {node.computeKind}
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        {node.description && (
          <div>
            <h4 className="text-sm font-medium text-slate-400 mb-1">Description</h4>
            <p className="text-sm text-slate-300">{node.description}</p>
          </div>
        )}

        {/* Dependencies */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <ArrowUpRight className="w-4 h-4" />
              <span className="text-xs font-medium">Upstream</span>
            </div>
            <div className="text-xl font-bold text-slate-100">{node.upstreamCount}</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <ArrowDownLeft className="w-4 h-4" />
              <span className="text-xs font-medium">Downstream</span>
            </div>
            <div className="text-xl font-bold text-slate-100">{node.downstreamCount}</div>
          </div>
        </div>

        {/* Last Materialization */}
        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-slate-400 mb-1">
            <Clock className="w-4 h-4" />
            <span className="text-xs font-medium">Last Materialized</span>
          </div>
          <div className="text-slate-100">{lastMaterialized}</div>
        </div>

        {/* Group */}
        {node.groupName && (
          <div>
            <h4 className="text-sm font-medium text-slate-400 mb-1">Group</h4>
            <span className="px-2 py-1 text-sm bg-slate-700 text-slate-300 rounded">
              {node.groupName}
            </span>
          </div>
        )}

        {/* Impact Analysis */}
        {node.downstreamCount > 0 && (
          <ImpactAnalysisSection assetKey={node.keyPath} downstreamCount={node.downstreamCount} onFocusGraph={onFocusGraph} />
        )}
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-slate-700 space-y-2">
        <Link
          to="/assets/$assetId"
          params={{ assetId: node.keyPath }}
          className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          View Details
        </Link>
        <button
          onClick={() => onFocusGraph(node.keyPath)}
          className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg transition-colors"
        >
          <GitBranch className="w-4 h-4" />
          Focus on This Asset
        </button>
      </div>
    </div>
  )
}

function LayerBadge({ layer }: { layer: string }) {
  const colors: Record<string, string> = {
    source: 'bg-blue-900/50 text-blue-300 border-blue-500',
    bronze: 'bg-amber-900/50 text-amber-300 border-amber-500',
    silver: 'bg-slate-700/50 text-slate-300 border-slate-400',
    gold: 'bg-yellow-900/50 text-yellow-300 border-yellow-500',
    publish: 'bg-emerald-900/50 text-emerald-300 border-emerald-500',
    unknown: 'bg-slate-800/50 text-slate-400 border-slate-600',
  }

  const labelMap: Record<string, string> = {
    source: 'Source',
    bronze: 'Bronze',
    silver: 'Silver',
    gold: 'Gold',
    publish: 'Published',
    unknown: 'Unknown',
  }

  return (
    <span className={`px-2 py-0.5 text-xs font-medium border rounded ${colors[layer] || colors.unknown}`}>
      {labelMap[layer] || layer}
    </span>
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

interface ImpactAnalysisSectionProps {
  assetKey: string
  downstreamCount: number
  onFocusGraph: (keyPath: string) => void
}

function ImpactAnalysisSection({ assetKey, downstreamCount, onFocusGraph }: ImpactAnalysisSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [impactedAssets, setImpactedAssets] = useState<Array<ImpactedAsset>>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isExpanded && impactedAssets.length === 0) {
      setLoading(true)
      getAssetImpact({ data: { assetKey } })
        .then(result => {
          if (!('error' in result)) {
            setImpactedAssets(result)
          }
        })
        .finally(() => setLoading(false))
    }
  }, [isExpanded, assetKey, impactedAssets.length])

  // Reset when asset changes
  useEffect(() => {
    setIsExpanded(false)
    setImpactedAssets([])
  }, [assetKey])

  const layerColors: Record<string, string> = {
    source: 'text-blue-400',
    bronze: 'text-amber-400',
    silver: 'text-slate-300',
    gold: 'text-yellow-400',
    publish: 'text-emerald-400',
    unknown: 'text-slate-500',
  }

  return (
    <div className="border border-orange-500/30 bg-orange-950/20 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full p-3 hover:bg-orange-950/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-medium text-orange-300">Impact Analysis</span>
          <span className="px-1.5 py-0.5 text-xs bg-orange-500/30 text-orange-300 rounded">
            {downstreamCount}
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-orange-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-orange-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-orange-500/20 p-2 max-h-48 overflow-y-auto">
          {loading ? (
            <div className="text-sm text-slate-400 text-center py-2">Loading...</div>
          ) : impactedAssets.length > 0 ? (
            <ul className="space-y-1">
              {impactedAssets.map(asset => (
                <li key={asset.keyPath}>
                  <button
                    onClick={() => onFocusGraph(asset.keyPath)}
                    className="flex items-center gap-2 w-full px-2 py-1.5 text-left text-sm hover:bg-slate-700/50 rounded transition-colors"
                  >
                    <span className={`${layerColors[asset.layer]} font-medium truncate flex-1`}>
                      {asset.label}
                    </span>
                    <span className="text-xs text-slate-500">
                      +{asset.depth} hop{asset.depth > 1 ? 's' : ''}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-sm text-slate-400 text-center py-2">No downstream assets</div>
          )}
        </div>
      )}
    </div>
  )
}

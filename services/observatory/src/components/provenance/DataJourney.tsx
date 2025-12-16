/**
 * Data Journey Component
 *
 * React Flow visualization showing the data lineage path for an asset.
 * Shows upstream sources → current asset → downstream consumers.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Database, GitBranch, Loader2 } from 'lucide-react'

import type { GraphNode } from '@/server/graph.server'
import type { Edge, Node, NodeProps } from '@xyflow/react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getAssetNeighbors } from '@/server/graph.server'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { formatDate } from '@/utils/dateFormat'

interface DataJourneyProps {
  assetKey: string
  className?: string
}

// Custom node component for journey visualization
function JourneyNode({ data }: NodeProps) {
  const isCurrent = data.isCurrent as boolean
  const computeKind = data.computeKind as string | undefined
  const lastMaterialized = data.lastMaterialized as string | undefined

  return (
    <div
      className={cn(
        'px-4 py-3 border border-border border-l-4 bg-card shadow-sm',
        'transition-colors hover:bg-muted/50',
        isCurrent
          ? 'border-l-primary ring-2 ring-primary/40'
          : 'border-l-border',
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />

      <div className="flex items-center gap-2 mb-1">
        <Database
          className={cn(
            'w-4 h-4',
            isCurrent ? 'text-primary' : 'text-muted-foreground',
          )}
        />
        <span className="font-medium text-sm">{data.label as string}</span>
      </div>

      <div className="flex items-center gap-2 text-xs">
        {computeKind && <Badge variant="outline">{computeKind}</Badge>}
        {lastMaterialized && (
          <span className="text-muted-foreground">{lastMaterialized}</span>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="!bg-border" />
    </div>
  )
}

const nodeTypes = {
  journey: JourneyNode,
}

export function DataJourney({ assetKey, className = '' }: DataJourneyProps) {
  const [graphData, setGraphData] = useState<{
    nodes: Array<GraphNode>
    edges: Array<{ source: string; target: string }>
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { settings } = useObservatorySettings()

  // Load asset neighbors
  useEffect(() => {
    async function loadGraph() {
      setLoading(true)
      setError(null)
      try {
        const result = await getAssetNeighbors({
          data: {
            assetKey,
            direction: 'both',
            depth: 2,
            dagsterUrl: settings.connections.dagsterGraphqlUrl,
          },
        })
        if ('error' in result) {
          setError(result.error)
        } else {
          setGraphData(result)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lineage')
      } finally {
        setLoading(false)
      }
    }
    loadGraph()
  }, [assetKey, settings.connections.dagsterGraphqlUrl])

  // Convert graph data to React Flow format
  const { nodes, edges } = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] }

    // Calculate horizontal layout based on depth from current asset
    const currentNode = graphData.nodes.find((n) => n.keyPath === assetKey)
    if (!currentNode) return { nodes: [], edges: [] }

    // BFS to find depths
    const depths = new Map<string, number>()
    depths.set(assetKey, 0)

    // Find upstream nodes (negative depth)
    const upstreamQueue = [assetKey]
    while (upstreamQueue.length > 0) {
      const current = upstreamQueue.shift()!
      const currentDepth = depths.get(current)!

      for (const edge of graphData.edges) {
        if (edge.target === current && !depths.has(edge.source)) {
          depths.set(edge.source, currentDepth - 1)
          upstreamQueue.push(edge.source)
        }
      }
    }

    // Find downstream nodes (positive depth)
    const downstreamQueue = [assetKey]
    while (downstreamQueue.length > 0) {
      const current = downstreamQueue.shift()!
      const currentDepth = depths.get(current)!

      for (const edge of graphData.edges) {
        if (edge.source === current && !depths.has(edge.target)) {
          depths.set(edge.target, currentDepth + 1)
          downstreamQueue.push(edge.target)
        }
      }
    }

    // Group nodes by depth
    const nodesByDepth = new Map<number, Array<GraphNode>>()
    for (const node of graphData.nodes) {
      const depth = depths.get(node.keyPath) ?? 0
      if (!nodesByDepth.has(depth)) {
        nodesByDepth.set(depth, [])
      }
      nodesByDepth.get(depth)!.push(node)
    }

    // Position nodes
    const flowNodes: Array<Node> = []
    const xSpacing = 280
    const ySpacing = 80

    const sortedDepths = Array.from(nodesByDepth.keys()).sort((a, b) => a - b)
    const minDepth = sortedDepths[0] ?? 0

    for (const [depth, nodesAtDepth] of nodesByDepth) {
      const xPos = (depth - minDepth) * xSpacing
      const startY = -((nodesAtDepth.length - 1) * ySpacing) / 2

      nodesAtDepth.forEach((node, idx) => {
        flowNodes.push({
          id: node.keyPath,
          type: 'journey',
          position: { x: xPos, y: startY + idx * ySpacing },
          data: {
            label: node.keyPath.split('/').pop() || node.keyPath,
            isCurrent: node.keyPath === assetKey,
            computeKind: node.computeKind,
            lastMaterialized: node.lastMaterialization
              ? formatRelativeTime(
                  new Date(Number(node.lastMaterialization)),
                  settings.ui.dateFormat,
                )
              : undefined,
          },
        })
      })
    }

    // Create edges
    const flowEdges: Array<Edge> = graphData.edges.map((edge) => ({
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: 'var(--border)', strokeWidth: 2 },
      animated: edge.source === assetKey || edge.target === assetKey,
    }))

    return { nodes: flowNodes, edges: flowEdges }
  }, [graphData, assetKey, settings.ui.dateFormat])

  const onInit = useCallback(() => {
    // Fit to view on init
  }, [])

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center h-64', className)}>
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div
        className={`flex items-center justify-center h-64 text-red-400 ${className}`}
      >
        <p>{error}</p>
      </div>
    )
  }

  if (nodes.length === 0) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center h-64 text-muted-foreground',
          className,
        )}
      >
        <GitBranch className="w-8 h-8 mb-2 opacity-50" />
        <p>No lineage data available</p>
      </div>
    )
  }

  return (
    <div className={cn('h-80 bg-background border border-border', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onInit={onInit}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        panOnDrag
        zoomOnScroll
      >
        <Background color="var(--border)" gap={16} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}

// Utility
function formatRelativeTime(date: Date, mode: 'iso' | 'local'): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(date, mode)
}

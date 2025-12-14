/**
 * GraphCanvas Component
 *
 * Interactive asset lineage graph using React Flow.
 * Displays nodes colored by data layer and edges showing dependencies.
 */

import { useCallback, useMemo } from 'react'

import { useNavigate } from '@tanstack/react-router'
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Database } from 'lucide-react'

import type { GraphEdge, GraphNode } from '@/server/graph.server'
import type { Edge, Node, NodeProps, NodeTypes } from '@xyflow/react'

const LAYER_STYLES: Record<
  string,
  { accentBorder: string; icon: string; label: string }
> = {
  source: {
    accentBorder: 'border-l-emerald-400/60',
    icon: 'text-emerald-400',
    label: 'text-foreground',
  },
  bronze: {
    accentBorder: 'border-l-amber-400/70',
    icon: 'text-amber-400',
    label: 'text-foreground',
  },
  silver: {
    accentBorder: 'border-l-border',
    icon: 'text-muted-foreground',
    label: 'text-foreground',
  },
  gold: {
    accentBorder: 'border-l-primary',
    icon: 'text-primary',
    label: 'text-foreground',
  },
  publish: {
    accentBorder: 'border-l-emerald-400/60',
    icon: 'text-emerald-400',
    label: 'text-foreground',
  },
  unknown: {
    accentBorder: 'border-l-border',
    icon: 'text-muted-foreground',
    label: 'text-foreground',
  },
}

interface AssetNodeData {
  label: string
  keyPath: string
  layer: string
  computeKind?: string
  description?: string
  onSelect: (keyPath: string) => void
  [key: string]: unknown // Index signature for React Flow compatibility
}

// Custom node component for assets
function AssetNode({ data, selected }: NodeProps<AssetNodeData>) {
  const styles = LAYER_STYLES[data.layer] || LAYER_STYLES.unknown

  return (
    <>
      <Handle type="target" position={Position.Left} className="!bg-border" />
      <div
        className={[
          'min-w-[160px] cursor-pointer border border-border border-l-4 bg-card px-3 py-2 shadow-sm transition-colors',
          'hover:bg-muted/50',
          styles.accentBorder,
          selected ? 'ring-2 ring-primary/40' : '',
        ].join(' ')}
        onClick={() => data.onSelect(data.keyPath)}
      >
        <div className="flex items-center gap-2">
          <Database className={`w-4 h-4 ${styles.icon}`} />
          <span className={`text-sm font-medium ${styles.label}`}>
            {data.label}
          </span>
        </div>
        {data.computeKind && (
          <div className="mt-1 text-xs text-muted-foreground">
            {data.computeKind}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-border" />
    </>
  )
}

const nodeTypes: NodeTypes = {
  asset: AssetNode,
}

interface GraphCanvasProps {
  graphNodes: Array<GraphNode>
  graphEdges: Array<GraphEdge>
  focusedAsset?: string
  onAssetSelect: (keyPath: string) => void
}

export function GraphCanvas({
  graphNodes,
  graphEdges,
  focusedAsset,
  onAssetSelect,
}: GraphCanvasProps) {
  const navigate = useNavigate()

  // Convert graph data to React Flow format
  const initialNodes = useMemo(() => {
    // Position nodes using a simple layered layout
    const layerOrder = [
      'source',
      'bronze',
      'silver',
      'gold',
      'publish',
      'unknown',
    ]
    const layerX: Record<string, number> = {}
    layerOrder.forEach((layer, i) => {
      layerX[layer] = i * 250
    })

    // Count nodes per layer to position vertically
    const layerCounts: Record<string, number> = {}

    return graphNodes.map((node): Node<AssetNodeData> => {
      const layer = node.layer
      if (!layerCounts[layer]) layerCounts[layer] = 0
      const yIndex = layerCounts[layer]++

      return {
        id: node.keyPath,
        type: 'asset',
        position: {
          x: layerX[layer] || 0,
          y: yIndex * 80,
        },
        data: {
          label: node.label,
          keyPath: node.keyPath,
          layer: node.layer,
          computeKind: node.computeKind,
          description: node.description,
          onSelect: onAssetSelect,
        },
        selected: node.keyPath === focusedAsset,
      }
    })
  }, [graphNodes, focusedAsset, onAssetSelect])

  const initialEdges = useMemo(() => {
    return graphEdges.map(
      (edge, i): Edge => ({
        id: `edge-${i}`,
        source: edge.source,
        target: edge.target,
        animated: false,
        style: { stroke: 'var(--border)', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'var(--border)',
        },
      }),
    )
  }, [graphEdges])

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onAssetSelect(node.id)
    },
    [onAssetSelect],
  )

  const handleNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      navigate({ to: '/assets/$assetId', params: { assetId: node.id } })
    },
    [navigate],
  )

  // MiniMap node color
  const miniMapNodeColor = useCallback((node: Node) => {
    const layer = (node.data as AssetNodeData)?.layer || 'unknown'
    const colorMap: Record<string, string> = {
      source: '#34d399',
      bronze: '#f59e0b',
      silver: '#a1a1aa',
      gold: '#fbbf24',
      publish: '#34d399',
      unknown: '#a1a1aa',
    }
    return colorMap[layer] || colorMap.unknown
  }, [])

  return (
    <div className="w-full h-full bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeDoubleClick={handleNodeDoubleClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        className="bg-background"
      >
        <Background color="var(--border)" gap={20} />
        <Controls className="!bg-card !border-border !rounded-none [&>button]:!bg-card [&>button]:!border-border [&>button]:!fill-muted-foreground [&>button:hover]:!bg-muted" />
        <MiniMap
          nodeColor={miniMapNodeColor}
          maskColor="rgba(0, 0, 0, 0.6)"
          className="!bg-card !border-border !rounded-none"
        />
      </ReactFlow>
    </div>
  )
}

// Legend component for the graph
export function GraphLegend() {
  const layers = [
    { key: 'source', label: 'Source/Ingestion' },
    { key: 'bronze', label: 'Bronze' },
    { key: 'silver', label: 'Silver' },
    { key: 'gold', label: 'Gold' },
    { key: 'publish', label: 'Published' },
  ]

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-card/80 backdrop-blur-sm border border-border">
      <span className="text-xs text-muted-foreground font-medium">Layers:</span>
      {layers.map(({ key, label }) => {
        const styles = LAYER_STYLES[key] || LAYER_STYLES.unknown
        return (
          <div key={key} className="flex items-center gap-1.5">
            <div
              className={[
                'h-3 w-3 border border-border bg-card',
                styles.accentBorder,
              ].join(' ')}
            />
            <span className="text-xs text-muted-foreground">{label}</span>
          </div>
        )
      })}
    </div>
  )
}

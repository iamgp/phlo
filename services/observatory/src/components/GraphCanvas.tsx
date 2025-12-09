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
import type { Edge, Node, NodeTypes } from '@xyflow/react'

// Layer colors matching the design spec
const LAYER_COLORS: Record<
  string,
  { bg: string; border: string; text: string }
> = {
  source: {
    bg: 'bg-blue-900/50',
    border: 'border-blue-500',
    text: 'text-blue-300',
  },
  bronze: {
    bg: 'bg-amber-900/50',
    border: 'border-amber-500',
    text: 'text-amber-300',
  },
  silver: {
    bg: 'bg-slate-700/50',
    border: 'border-slate-400',
    text: 'text-slate-300',
  },
  gold: {
    bg: 'bg-yellow-900/50',
    border: 'border-yellow-500',
    text: 'text-yellow-300',
  },
  publish: {
    bg: 'bg-emerald-900/50',
    border: 'border-emerald-500',
    text: 'text-emerald-300',
  },
  unknown: {
    bg: 'bg-slate-800/50',
    border: 'border-slate-600',
    text: 'text-slate-400',
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
function AssetNode({ data }: { data: AssetNodeData }) {
  const colors = LAYER_COLORS[data.layer] || LAYER_COLORS.unknown

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-slate-500"
      />
      <div
        className={`px-3 py-2 rounded-lg border-2 ${colors.bg} ${colors.border} min-w-[140px] cursor-pointer hover:brightness-110 transition-all`}
        onClick={() => data.onSelect(data.keyPath)}
      >
        <div className="flex items-center gap-2">
          <Database className={`w-4 h-4 ${colors.text}`} />
          <span className={`text-sm font-medium ${colors.text}`}>
            {data.label}
          </span>
        </div>
        {data.computeKind && (
          <div className="mt-1 text-xs text-slate-500">{data.computeKind}</div>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className="!bg-slate-500"
      />
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
        style: { stroke: '#475569', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#475569',
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
      source: '#3b82f6',
      bronze: '#d97706',
      silver: '#64748b',
      gold: '#eab308',
      publish: '#10b981',
      unknown: '#475569',
    }
    return colorMap[layer] || colorMap.unknown
  }, [])

  return (
    <div className="w-full h-full bg-slate-900">
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
        className="bg-slate-900"
      >
        <Background color="#334155" gap={20} />
        <Controls className="!bg-slate-800 !border-slate-700 !rounded-lg [&>button]:!bg-slate-700 [&>button]:!border-slate-600 [&>button]:!fill-slate-300 [&>button:hover]:!bg-slate-600" />
        <MiniMap
          nodeColor={miniMapNodeColor}
          maskColor="rgba(15, 23, 42, 0.8)"
          className="!bg-slate-800 !border-slate-700 !rounded-lg"
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
    <div className="flex items-center gap-4 px-4 py-2 bg-slate-800/80 backdrop-blur-sm rounded-lg border border-slate-700">
      <span className="text-xs text-slate-400 font-medium">Layers:</span>
      {layers.map(({ key, label }) => {
        const colors = LAYER_COLORS[key]
        return (
          <div key={key} className="flex items-center gap-1.5">
            <div
              className={`w-3 h-3 rounded ${colors.bg} ${colors.border} border`}
            />
            <span className={`text-xs ${colors.text}`}>{label}</span>
          </div>
        )
      })}
    </div>
  )
}

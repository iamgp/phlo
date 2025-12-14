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
  marts: {
    accentBorder: 'border-l-emerald-400/60',
    icon: 'text-emerald-400',
    label: 'text-foreground',
  },
  publish: {
    accentBorder: 'border-l-lime-400/70',
    icon: 'text-lime-400',
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

type AssetNodeType = Node<AssetNodeData, 'asset'>

// Custom node component for assets
function AssetNode({ data, selected }: NodeProps<AssetNodeType>) {
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

const LAYER_X: Record<string, number> = {
  source: 0,
  bronze: 240,
  // Keep DLT → STG visually tighter.
  silver: 440,
  gold: 690,
  marts: 930,
  // Make publishing feel separate from marts/warehouse.
  publish: 1280,
  unknown: 1520,
}

const LAYER_ORDER = [
  'source',
  'bronze',
  'silver',
  'gold',
  'marts',
  'publish',
  'unknown',
] as const

type LayerKey = (typeof LAYER_ORDER)[number]

function computeLayeredNodeOrder({
  nodes,
  edges,
}: {
  nodes: Array<GraphNode>
  edges: Array<GraphEdge>
}): Record<string, number> {
  const layerById = new Map<string, LayerKey>()
  const layerIndex = new Map<LayerKey, number>()
  LAYER_ORDER.forEach((layer, idx) => layerIndex.set(layer, idx))

  for (const node of nodes) {
    layerById.set(node.keyPath, node.layer)
  }

  const byLayer = new Map<LayerKey, Array<string>>()
  for (const layer of LAYER_ORDER) byLayer.set(layer, [])

  for (const node of nodes) {
    const layer = node.layer ?? 'unknown'
    byLayer.get(layer)?.push(node.keyPath)
  }

  // Start deterministic (so layout doesn't "jump" between refreshes)
  for (const layer of LAYER_ORDER) {
    byLayer.get(layer)!.sort((a, b) => a.localeCompare(b))
  }

  const incoming = new Map<string, Array<string>>()
  const outgoing = new Map<string, Array<string>>()
  for (const { source, target } of edges) {
    if (!incoming.has(target)) incoming.set(target, [])
    incoming.get(target)!.push(source)
    if (!outgoing.has(source)) outgoing.set(source, [])
    outgoing.get(source)!.push(target)
  }

  const positionsInLayer = () => {
    const pos = new Map<string, number>()
    for (const layer of LAYER_ORDER) {
      byLayer.get(layer)!.forEach((id, idx) => pos.set(id, idx))
    }
    return pos
  }

  const orderByBarycenter = (
    layer: LayerKey,
    neighborLayerPredicate: (
      neighborLayerIndex: number,
      thisLayerIndex: number,
    ) => boolean,
    neighborGetter: (id: string) => Array<string>,
  ) => {
    const thisLayerIndex = layerIndex.get(layer) ?? 0
    const pos = positionsInLayer()

    const scored = byLayer.get(layer)!.map((id, originalIndex) => {
      const neighbors = neighborGetter(id)
      const neighborPositions: Array<number> = []
      for (const n of neighbors) {
        const nLayer = layerById.get(n)
        if (!nLayer) continue
        const nLayerIndex = layerIndex.get(nLayer) ?? 0
        if (!neighborLayerPredicate(nLayerIndex, thisLayerIndex)) continue
        const p = pos.get(n)
        if (p !== undefined) neighborPositions.push(p)
      }

      if (neighborPositions.length === 0) {
        return { id, score: Number.POSITIVE_INFINITY, originalIndex }
      }

      const avg =
        neighborPositions.reduce((sum, v) => sum + v, 0) /
        neighborPositions.length
      return { id, score: avg, originalIndex }
    })

    scored.sort((a, b) => {
      if (a.score === b.score) return a.originalIndex - b.originalIndex
      if (a.score === Number.POSITIVE_INFINITY) return 1
      if (b.score === Number.POSITIVE_INFINITY) return -1
      return a.score - b.score
    })

    byLayer.set(
      layer,
      scored.map((s) => s.id),
    )
  }

  // A couple of sweeps is enough for our scale (< ~1k nodes) without a full layout engine.
  for (let i = 0; i < 3; i += 1) {
    // Left-to-right (use upstream / incoming)
    for (const layer of LAYER_ORDER) {
      orderByBarycenter(
        layer,
        (nLayerIndex, thisLayerIndex) => nLayerIndex < thisLayerIndex,
        (id) => incoming.get(id) ?? [],
      )
    }
    // Right-to-left (use downstream / outgoing)
    for (const layer of [...LAYER_ORDER].reverse()) {
      orderByBarycenter(
        layer,
        (nLayerIndex, thisLayerIndex) => nLayerIndex > thisLayerIndex,
        (id) => outgoing.get(id) ?? [],
      )
    }
  }

  const finalOrderIndex = new Map<string, number>()
  for (const layer of LAYER_ORDER) {
    byLayer.get(layer)!.forEach((id, idx) => finalOrderIndex.set(id, idx))
  }

  return Object.fromEntries(finalOrderIndex.entries())
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
    const orderIndexById = computeLayeredNodeOrder({
      nodes: graphNodes,
      edges: graphEdges,
    })

    return graphNodes.map((node): Node<AssetNodeData> => {
      const layer = node.layer
      const yIndex = orderIndexById[node.keyPath] ?? 0

      return {
        id: node.keyPath,
        type: 'asset',
        position: {
          x: LAYER_X[layer] ?? LAYER_X.unknown,
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
        type: 'smoothstep',
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
      marts: '#34d399',
      publish: '#a3e635',
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
    { key: 'marts', label: 'Marts' },
    { key: 'publish', label: 'Publishing' },
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

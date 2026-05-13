import { useCallback, useMemo } from 'react'

import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  Database,
  GitBranch,
  RotateCcw,
  ShieldCheck,
  Table2,
} from 'lucide-react'

import type { Edge, Node, NodeProps, NodeTypes } from '@xyflow/react'
import type { MouseEvent } from 'react'

type V2FlowNodeKind =
  | 'asset'
  | 'table'
  | 'quality'
  | 'operation'
  | 'branch'
  | 'service'

export interface V2FlowNode {
  id: string
  label: string
  kind: V2FlowNodeKind
  selectId?: string | null
  lane?: string | null
  subtitle?: string | null
  metric?: string | null
}

export interface V2FlowEdge {
  id: string
  source: string
  target: string
  label?: string | null
}

interface FlowNodeData extends Record<string, unknown> {
  label: string
  kind: V2FlowNodeKind
  lane: string
  selectId?: string | null
  subtitle?: string | null
  metric?: string | null
}

const laneX: Record<string, number> = {
  raw: 0,
  bronze: 220,
  silver: 440,
  gold: 680,
  marts: 900,
  branch: 0,
  table: 260,
  quality: 540,
  operation: 260,
  service: 0,
  other: 820,
}

const kindIcon = {
  asset: Database,
  table: Table2,
  quality: ShieldCheck,
  operation: RotateCcw,
  branch: GitBranch,
  service: Database,
} satisfies Record<V2FlowNodeKind, typeof Database>

function FlowNode({ data, selected }: NodeProps<Node<FlowNodeData, 'phlo'>>) {
  const Icon = kindIcon[data.kind]

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        className="phlo-v2-flow-handle"
      />
      <div
        className="phlo-v2-flow-node"
        data-kind={data.kind}
        data-selected={selected ? 'true' : 'false'}
      >
        <div className="phlo-v2-flow-node-title">
          <span className="phlo-v2-flow-node-mark">
            <Icon className="size-3.5" />
          </span>
          <span>{data.label}</span>
        </div>
        <div className="phlo-v2-flow-node-meta">
          <span>{data.lane}</span>
          {data.metric && <span>{data.metric}</span>}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className="phlo-v2-flow-handle"
      />
    </>
  )
}

const nodeTypes: NodeTypes = {
  phlo: FlowNode,
}

export function V2FlowCanvas({
  nodes: graphNodes,
  edges: graphEdges,
  selectedId,
  onSelect,
}: {
  nodes: Array<V2FlowNode>
  edges: Array<V2FlowEdge>
  selectedId?: string | null
  onSelect?: (id: string) => void
}) {
  const initialNodes = useMemo(() => {
    const laneCounts = new Map<string, number>()

    return graphNodes.map((graphNode): Node<FlowNodeData, 'phlo'> => {
      const lane = graphNode.lane || graphNode.kind || 'other'
      const index = laneCounts.get(lane) ?? 0
      laneCounts.set(lane, index + 1)

      return {
        id: graphNode.id,
        type: 'phlo',
        position: {
          x: laneX[lane] ?? laneX.other,
          y: index * 112,
        },
        data: {
          label: graphNode.label,
          kind: graphNode.kind,
          lane,
          selectId: graphNode.selectId ?? graphNode.id,
          subtitle: graphNode.subtitle,
          metric: graphNode.metric,
        },
        selected: graphNode.id === selectedId,
      }
    })
  }, [graphNodes, selectedId])

  const initialEdges = useMemo(
    () =>
      graphEdges.map(
        (edge): Edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.label ?? undefined,
          type: 'smoothstep',
          style: { stroke: 'var(--v2-sheet-border)', strokeWidth: 2 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: 'var(--v2-sheet-border)',
          },
        }),
      ),
    [graphEdges],
  )
  const canvasKey = `${selectedId ?? 'none'}:${graphNodes
    .map(
      (node) =>
        `${node.id}:${node.label}:${node.lane ?? ''}:${node.metric ?? ''}:${node.subtitle ?? ''}`,
    )
    .join('|')}:${graphEdges
    .map(
      (edge) => `${edge.id}:${edge.source}:${edge.target}:${edge.label ?? ''}`,
    )
    .join('|')}`

  return (
    <V2FlowCanvasInstance
      key={canvasKey}
      edges={initialEdges}
      nodes={initialNodes}
      onSelect={onSelect}
    />
  )
}

function V2FlowCanvasInstance({
  edges: initialEdges,
  nodes: initialNodes,
  onSelect,
}: {
  edges: Array<Edge>
  nodes: Array<Node<FlowNodeData, 'phlo'>>
  onSelect?: (id: string) => void
}) {
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  const handleNodeClick = useCallback(
    (_: MouseEvent, node: Node) => {
      onSelect?.(String(node.data.selectId ?? node.id))
    },
    [onSelect],
  )

  return (
    <div className="phlo-v2-flow-canvas">
      {nodes.length > 0 ? (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={handleNodeClick}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          fitViewOptions={{ padding: 0.24, maxZoom: 0.9 }}
          minZoom={0.15}
          maxZoom={1.8}
        >
          <Background color="var(--v2-sheet-border)" gap={20} />
          <Controls className="phlo-v2-flow-controls" />
        </ReactFlow>
      ) : (
        <div className="phlo-v2-flow-empty">
          <Database className="size-4" />
          <span>No graph nodes yet</span>
        </div>
      )}
    </div>
  )
}

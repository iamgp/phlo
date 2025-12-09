/**
 * Row Journey Component
 *
 * Enhanced journey visualization that shows row data, transformation SQL,
 * and quality checks for each asset in the lineage.
 *
 * phlo-lx7: Node details now shown in panel below flow instead of inline expansion.
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
import { AlertCircle, CheckCircle, Code, Database, Loader2 } from 'lucide-react'
import { Highlight, themes } from 'prism-react-renderer'
import type { DataRow } from '@/server/trino.server'
import type { Edge, Node, NodeProps } from '@xyflow/react'
import { getAssetDetails } from '@/server/dagster.server'
import { getAssetNeighbors } from '@/server/graph.server'
import { getAssetChecks } from '@/server/quality.server'
import { executeQuery } from '@/server/trino.server'
import {
  analyzeSQLTransformation,
  buildUpstreamWhereClause,
} from '@/utils/sqlParser'
import '@xyflow/react/dist/style.css'

interface RowJourneyProps {
  assetKey: string
  rowData: Record<string, unknown>
  columnTypes: Array<string>
  className?: string
}

interface AssetNodeData {
  label: string
  isCurrent: boolean
  computeKind?: string
  assetKey: string
  onSelect: (assetKey: string) => void
  [key: string]: unknown // Allow index signature for React Flow
}

interface NodeDetails {
  sql?: string
  checks?: Array<{ name: string; status: string }>
  stageData?: Array<DataRow>
}

// Simple node component - click to select (phlo-lx7)
function JourneyNode({ data }: NodeProps) {
  const isCurrent = data.isCurrent as boolean
  const assetKey = data.assetKey as string
  const onSelect = data.onSelect as (key: string) => void

  return (
    <div
      onClick={() => onSelect(assetKey)}
      className={`rounded-lg border-2 transition-all cursor-pointer ${
        isCurrent
          ? 'bg-cyan-900/50 border-cyan-400 shadow-lg shadow-cyan-500/20'
          : 'bg-slate-800 border-slate-600 hover:border-cyan-500 hover:bg-slate-700'
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-slate-500"
      />

      <div className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Database
            className={`w-4 h-4 ${isCurrent ? 'text-cyan-400' : 'text-slate-400'}`}
          />
          <span
            className={`font-medium text-sm ${isCurrent ? 'text-cyan-100' : 'text-slate-200'}`}
          >
            {data.label as string}
          </span>
        </div>

        {data.computeKind ? (
          <span className="mt-1 inline-block px-1.5 py-0.5 bg-purple-900/50 text-purple-300 rounded text-xs">
            {String(data.computeKind)}
          </span>
        ) : null}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="!bg-slate-500"
      />
    </div>
  )
}

const nodeTypes = {
  journey: JourneyNode,
}

// Detail panel component shown below the flow (phlo-lx7)
function NodeDetailPanel({
  assetKey,
  isLoading,
  details,
}: {
  assetKey: string
  isLoading: boolean
  details: NodeDetails | null
}) {
  const tableName = assetKey.split('/').pop() || assetKey

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
          <span className="text-slate-400">
            Loading details for {tableName}...
          </span>
        </div>
      </div>
    )
  }

  if (!details) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-center text-slate-500">
        <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Click a node above to view its details</p>
      </div>
    )
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      <div className="p-4 border-b border-slate-700">
        <h4 className="font-medium text-slate-200 flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          {tableName}
        </h4>
      </div>

      <div className="p-4 space-y-4">
        {/* Transformation SQL */}
        {details.sql && (
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-300 mb-2 font-medium">
              <Code className="w-4 h-4" />
              Transformation SQL
            </div>
            <Highlight
              theme={themes.nightOwl}
              code={cleanSqlForDisplay(details.sql)}
              language="sql"
            >
              {({ style, tokens, getLineProps, getTokenProps }) => (
                <pre
                  style={{ ...style, margin: 0 }}
                  className="p-3 rounded-lg text-xs overflow-x-auto max-h-64 leading-relaxed"
                >
                  {tokens.map((line, i) => (
                    <div key={i} {...getLineProps({ line })}>
                      {line.map((token, key) => (
                        <span key={key} {...getTokenProps({ token })} />
                      ))}
                    </div>
                  ))}
                </pre>
              )}
            </Highlight>
          </div>
        )}

        {/* Quality Checks */}
        {details.checks && details.checks.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-300 mb-2 font-medium">
              <CheckCircle className="w-4 h-4" />
              Quality Checks
            </div>
            <div className="flex flex-wrap gap-2">
              {details.checks.map((check) => (
                <div
                  key={check.name}
                  className="flex items-center gap-2 text-xs bg-slate-900 px-3 py-1.5 rounded"
                >
                  {check.status === 'PASSED' ? (
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  )}
                  <span className="text-slate-200">{check.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Row Data at this Stage */}
        {details.stageData && details.stageData.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-300 mb-2 font-medium">
              <Database className="w-4 h-4" />
              Contributing Source Rows from{' '}
              <code className="bg-slate-700 px-1.5 py-0.5 rounded text-cyan-300 ml-1">
                {tableName}
              </code>
              <span className="text-slate-500">
                ({details.stageData.length} row
                {details.stageData.length !== 1 ? 's' : ''})
              </span>
            </div>
            <div className="bg-slate-900 rounded overflow-auto max-h-64">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-slate-900">
                  <tr className="border-b border-slate-700">
                    {Object.keys(details.stageData[0]).map((col) => (
                      <th
                        key={col}
                        className="text-left py-2 px-3 font-medium text-slate-300 whitespace-nowrap"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {details.stageData.map((row, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-slate-700/50 hover:bg-slate-800/50"
                    >
                      {Object.values(row).map((val, colIdx) => (
                        <td
                          key={colIdx}
                          className="py-2 px-3 text-slate-200 font-mono whitespace-nowrap"
                        >
                          {val === null || val === undefined
                            ? '—'
                            : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* No data found */}
        {!details.sql &&
          (!details.checks || details.checks.length === 0) &&
          (!details.stageData || details.stageData.length === 0) && (
            <div className="text-sm text-slate-500">
              No additional details available for this asset.
            </div>
          )}
      </div>
    </div>
  )
}

// Clean SQL string for display by removing common prefixes
function cleanSqlForDisplay(sql: string): string {
  // Remove dbt model header, Raw SQL section, and markdown code fences
  const cleaned = sql
    // Remove "dbt model xxx" line at the start
    .replace(/^dbt\s+model\s+\S+\s*/i, '')
    // Remove "#### Raw SQL:" or similar headers
    .replace(/^#+\s*(Raw\s+)?SQL:\s*/im, '')
    // Remove markdown code fences
    .replace(/^```sql\s*/im, '')
    .replace(/```\s*$/im, '')
    // Also try a combined pattern for the full header block
    .replace(/^dbt\s+model\s+\S+[\s\S]*?```sql\s*/i, '')
    .trim()
  return cleaned
}

// Infer schema from table name prefixes
function inferSchemaFromTableName(tableName: string): string {
  const lower = tableName.toLowerCase()
  if (lower.startsWith('dlt_')) return 'bronze'
  if (lower.startsWith('stg_')) return 'silver'
  if (lower.startsWith('fct_') || lower.startsWith('dim_')) return 'gold'
  if (lower.startsWith('mrt_') || lower.startsWith('publish_')) return 'publish'
  return 'bronze' // default
}

export function RowJourney({
  assetKey,
  rowData,
  className = '',
}: RowJourneyProps) {
  const [graphData, setGraphData] = useState<{
    nodes: Array<{ keyPath: string; label: string; computeKind?: string }>
    edges: Array<{ source: string; target: string }>
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Selected node for detail panel (phlo-lx7)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [nodeDetails, setNodeDetails] = useState<NodeDetails | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)

  // Load asset neighbors
  useEffect(() => {
    async function loadGraph() {
      setLoading(true)
      setError(null)
      try {
        const result = await getAssetNeighbors({
          data: { assetKey, direction: 'both', depth: 2 },
        })
        if ('error' in result) {
          setError(result.error)
        } else {
          setGraphData(result)
          // Auto-select the current asset to show its details immediately
          setSelectedNode(assetKey)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lineage')
      } finally {
        setLoading(false)
      }
    }
    loadGraph()
  }, [assetKey])

  // Load details when node is selected (phlo-lx7)
  useEffect(() => {
    if (!selectedNode) {
      setNodeDetails(null)
      return
    }

    async function loadNodeDetails() {
      setDetailsLoading(true)
      try {
        const tableName = selectedNode!.split('/').pop() || selectedNode!
        const schema = inferSchemaFromTableName(tableName)

        // Fetch asset details and quality checks
        const [assetInfo, qualityInfo] = await Promise.all([
          getAssetDetails({ data: selectedNode! }),
          getAssetChecks({ data: { assetKey: selectedNode!.split('/') } }),
        ])

        const checks =
          'error' in qualityInfo
            ? []
            : qualityInfo.map((check) => ({
                name: check.name,
                status: check.status,
              }))

        const sql = 'error' in assetInfo ? undefined : assetInfo.description

        // Query upstream data using SQL parsing
        let stageData: Array<DataRow> | undefined

        if (rowData && sql) {
          try {
            const analysis = analyzeSQLTransformation(sql)
            const whereClause = buildUpstreamWhereClause(
              rowData,
              analysis.columnMappings,
            )

            if (whereClause) {
              const query = `SELECT * FROM iceberg.${schema}.${tableName} WHERE ${whereClause} LIMIT 10`
              const queryResult = await executeQuery({
                data: { query, branch: schema },
              })

              if (!('error' in queryResult)) {
                stageData = queryResult.rows
              }
            }
          } catch (parseErr) {
            console.warn('[RowJourney] Failed to parse SQL or query:', parseErr)
          }
        }

        setNodeDetails({ sql, checks, stageData })
      } catch (err) {
        console.error('Failed to load node details:', err)
        setNodeDetails(null)
      } finally {
        setDetailsLoading(false)
      }
    }

    loadNodeDetails()
  }, [selectedNode, rowData])

  // Handle node selection
  const handleNodeSelect = useCallback((nodeKey: string) => {
    setSelectedNode(nodeKey)
  }, [])

  // Convert graph data to React Flow format
  const { nodes, edges } = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] }

    // Calculate horizontal layout based on depth
    const currentNode = graphData.nodes.find((n) => n.keyPath === assetKey)
    if (!currentNode) return { nodes: [], edges: [] }

    // BFS to find depths
    const depths = new Map<string, number>()
    depths.set(assetKey, 0)

    // Find upstream nodes
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

    // Find downstream nodes
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
    const nodesByDepth = new Map<number, typeof graphData.nodes>()
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
    const ySpacing = 100

    const sortedDepths = Array.from(nodesByDepth.keys()).sort((a, b) => a - b)
    const minDepth = sortedDepths[0] ?? 0

    for (const [depth, nodesAtDepth] of nodesByDepth) {
      const xPos = (depth - minDepth) * xSpacing
      const startY = -((nodesAtDepth.length - 1) * ySpacing) / 2

      nodesAtDepth.forEach((node, idx) => {
        const isSelected = node.keyPath === selectedNode
        flowNodes.push({
          id: node.keyPath,
          type: 'journey',
          position: { x: xPos, y: startY + idx * ySpacing },
          selected: isSelected,
          data: {
            label: node.keyPath.split('/').pop() || node.keyPath,
            isCurrent: node.keyPath === assetKey,
            computeKind: node.computeKind,
            assetKey: node.keyPath,
            onSelect: handleNodeSelect,
          } as AssetNodeData,
        })
      })
    }

    // Create edges
    const flowEdges: Array<Edge> = graphData.edges.map((edge) => ({
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#475569', strokeWidth: 2 },
      animated: edge.source === assetKey || edge.target === assetKey,
    }))

    return { nodes: flowNodes, edges: flowEdges }
  }, [graphData, assetKey, selectedNode, handleNodeSelect])

  const onInit = useCallback(() => {
    // Fit to view on init
  }, [])

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
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
        className={`flex flex-col items-center justify-center h-64 text-slate-500 ${className}`}
      >
        <Database className="w-8 h-8 mb-2 opacity-50" />
        <p>No lineage data available</p>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Flow visualization */}
      <div className="h-72 bg-slate-900 rounded-xl border border-slate-700">
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
          <Background color="#334155" gap={16} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>

      {/* Detail panel below flow (phlo-lx7) */}
      <NodeDetailPanel
        assetKey={selectedNode || assetKey}
        isLoading={detailsLoading}
        details={nodeDetails}
      />
    </div>
  )
}

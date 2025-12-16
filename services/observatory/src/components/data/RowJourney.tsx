import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  AlertCircle,
  CheckCircle,
  Code,
  Database,
  Info,
  Loader2,
  Terminal,
} from 'lucide-react'
import { Highlight, themes } from 'prism-react-renderer'
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
} from '@xyflow/react'
import type { Edge, Node, NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import type { DataRow } from '@/server/trino.server'
import type { ContributingRowsPageResult } from '@/server/contributing.server'
import {
  getContributingRowsPage,
  getContributingRowsQuery,
} from '@/server/contributing.server'
import { getAssetDetails } from '@/server/dagster.server'
import { getAssetNeighbors } from '@/server/graph.server'
import { getAssetChecks } from '@/server/quality.server'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { ObservatoryTable } from '@/components/data/ObservatoryTable'
import { useObservatorySettings } from '@/hooks/useObservatorySettings'
import { cn } from '@/lib/utils'

interface RowJourneyProps {
  assetKey: string
  rowData: Record<string, unknown>
  columnTypes: Array<string>
  className?: string
  onQuerySource?: (query: string) => void
}

interface AssetNodeData {
  label: string
  isCurrent: boolean
  computeKind?: string
  assetKey: string
  onSelect: (assetKey: string) => void
  [key: string]: unknown // Allow index signature for React Flow
}

type JourneyNodeType = Node<AssetNodeData, 'journey'>

interface NodeDetails {
  sql?: string
  checks?: Array<{ name: string; status: string }>
  stageData?: Array<DataRow>
  upstreamAssetKeys?: Array<string>
}

function extractTransformationSql(asset: {
  description?: string
  metadata?: Array<{ key: string; value: string }>
}): string | undefined {
  const desc = asset.description?.trim()
  if (desc) return desc
  const candidates =
    asset.metadata
      ?.filter((m) => m.value && m.value.trim() && /sql/i.test(m.key))
      .sort((a, b) => b.value.length - a.value.length) ?? []
  return candidates[0]?.value?.trim() || undefined
}

// Simple node component - click to select
function JourneyNode({ data }: NodeProps<JourneyNodeType>) {
  const isCurrent = data.isCurrent
  const assetKey = data.assetKey
  const onSelect = data.onSelect

  return (
    <div
      onClick={() => onSelect(assetKey)}
      className={cn(
        'rounded-lg border-2 transition-colors cursor-pointer bg-card',
        isCurrent
          ? 'border-primary shadow-sm ring-1 ring-primary/20'
          : 'border-border hover:border-primary/50 hover:bg-muted/50',
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />

      <div className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Database
            className={cn(
              'w-4 h-4',
              isCurrent ? 'text-primary' : 'text-muted-foreground',
            )}
          />
          <span className="font-medium text-sm text-foreground">
            {data.label}
          </span>
        </div>

        {data.computeKind ? (
          <Badge variant="secondary" className="mt-2 text-xs">
            {String(data.computeKind)}
          </Badge>
        ) : null}
      </div>

      <Handle type="source" position={Position.Right} className="!bg-border" />
    </div>
  )
}

const nodeTypes = {
  journey: JourneyNode,
}

// Detail panel component shown below the flow
function NodeDetailPanel({
  assetKey,
  isLoading,
  details,
  rowData,
  onQuerySource,
}: {
  assetKey: string
  isLoading: boolean
  details: NodeDetails | null
  rowData: Record<string, unknown>
  onQuerySource?: (query: string) => void
}) {
  const { settings } = useObservatorySettings()
  const tableName = assetKey.split('/').pop() || assetKey
  const [contribOpen, setContribOpen] = useState(false)
  const [contribUpstreamAssetKey, setContribUpstreamAssetKey] = useState<
    string | null
  >(null)
  const [contribPage, setContribPage] = useState(0)
  const [contribPageSize, setContribPageSize] = useState(50)
  const [contribSeed, setContribSeed] = useState('phlo')
  const [contribLoading, setContribLoading] = useState(false)
  const [contribError, setContribError] = useState<string | null>(null)
  const [contribResult, setContribResult] = useState<Exclude<
    ContributingRowsPageResult,
    { error: string }
  > | null>(null)

  const loadContributingRows = useCallback(
    async (upstreamAssetKey: string) => {
      setContribLoading(true)
      setContribError(null)
      try {
        const result = await getContributingRowsPage({
          data: {
            downstreamAssetKey: assetKey,
            upstreamAssetKey,
            rowData,
            page: contribPage,
            pageSize: contribPageSize,
            seed: contribSeed,
            trinoUrl: settings.connections.trinoUrl,
            timeoutMs: settings.query.timeoutMs,
            catalog: settings.defaults.catalog,
          },
        })

        if ('error' in result) {
          setContribError(result.error)
          setContribResult(null)
          return
        }

        setContribResult(result)
      } catch (err) {
        setContribError(
          err instanceof Error
            ? err.message
            : 'Failed to load contributing rows',
        )
        setContribResult(null)
      } finally {
        setContribLoading(false)
      }
    },
    [
      assetKey,
      contribPage,
      contribPageSize,
      contribSeed,
      rowData,
      settings.connections.trinoUrl,
      settings.defaults.catalog,
      settings.query.timeoutMs,
    ],
  )

  useEffect(() => {
    if (!contribOpen) return
    if (!contribUpstreamAssetKey) return
    void loadContributingRows(contribUpstreamAssetKey)
  }, [contribOpen, contribUpstreamAssetKey, loadContributingRows])

  if (isLoading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
          <span className="text-muted-foreground">
            Loading details for {tableName}...
          </span>
        </div>
      </div>
    )
  }

  if (!details) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 text-center text-muted-foreground">
        <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Click a node above to view its details</p>
      </div>
    )
  }

  // Simple data row count message
  const getDataRowMessage = () => {
    const count = details.stageData?.length || 0
    const countLabel = `(${count} row${count !== 1 ? 's' : ''})`
    return { title: 'Source Data from', subtitle: countLabel }
  }

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <Sheet
        open={contribOpen}
        onOpenChange={(open) => {
          setContribOpen(open)
          if (!open) {
            setContribUpstreamAssetKey(null)
            setContribError(null)
            setContribResult(null)
            setContribPage(0)
          }
        }}
      >
        <SheetContent
          side="bottom"
          className="h-[85vh] sm:h-[75vh] sm:max-w-none"
        >
          <SheetHeader>
            <SheetTitle>Contributing rows</SheetTitle>
            <SheetDescription>
              {contribResult?.upstream
                ? `${contribResult.upstream.schema}.${contribResult.upstream.table}`
                : contribUpstreamAssetKey
                  ? contribUpstreamAssetKey.split('/').pop()
                  : ''}
            </SheetDescription>
          </SheetHeader>

          <div className="px-4 pb-4 flex flex-col gap-4 min-h-0 flex-1">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex flex-wrap items-end gap-3">
                <div className="grid gap-1">
                  <Label htmlFor="contrib-page-size">Page size</Label>
                  <select
                    id="contrib-page-size"
                    className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                    value={String(contribPageSize)}
                    onChange={(e) => {
                      setContribPageSize(Number(e.target.value))
                      setContribPage(0)
                    }}
                  >
                    <option value="25">25</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                    <option value="200">200</option>
                  </select>
                </div>

                {contribResult?.mode === 'aggregate' ? (
                  <div className="grid gap-1">
                    <div className="flex items-center gap-2">
                      <Label htmlFor="contrib-seed">Sampling</Label>
                      <Tooltip>
                        <TooltipTrigger
                          render={
                            <button
                              type="button"
                              className="text-muted-foreground hover:text-foreground"
                              aria-label="Sampling help"
                            />
                          }
                        >
                          <Info className="h-4 w-4" />
                        </TooltipTrigger>
                        <TooltipContent side="top">
                          Seed controls which rows you see for aggregate
                          contributors. Same seed = same sample.
                        </TooltipContent>
                      </Tooltip>
                    </div>
                    <Input
                      id="contrib-seed"
                      value={contribSeed}
                      onChange={(e) => {
                        setContribSeed(e.target.value)
                        setContribPage(0)
                      }}
                      className="w-56"
                    />
                  </div>
                ) : null}
              </div>

              <div className="flex items-center gap-2 self-start sm:self-auto">
                {contribResult?.mode ? (
                  <Badge variant="secondary" className="capitalize">
                    {contribResult.mode}
                  </Badge>
                ) : null}
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!contribResult?.query || !onQuerySource}
                  onClick={() => {
                    if (!contribResult?.query || !onQuerySource) return
                    onQuerySource(contribResult.query)
                  }}
                >
                  Open in SQL
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <div className="text-xs text-muted-foreground">
                Page {contribPage + 1}
                {contribResult
                  ? ` • ${contribResult.rows.length} row${
                      contribResult.rows.length === 1 ? '' : 's'
                    }`
                  : ''}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={contribPage === 0 || contribLoading}
                  onClick={() => setContribPage((p) => Math.max(0, p - 1))}
                >
                  Prev
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!contribResult?.hasMore || contribLoading}
                  onClick={() => setContribPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>

            {contribResult?.query ? (
              <details className="rounded-md border border-border bg-muted/30">
                <summary className="cursor-pointer select-none px-3 py-2 text-xs text-muted-foreground">
                  SQL (read-only)
                </summary>
                <div className="border-t border-border overflow-x-auto max-h-40">
                  <pre className="p-3 text-xs leading-relaxed">
                    {cleanSqlForDisplay(contribResult.query)}
                  </pre>
                </div>
              </details>
            ) : null}

            <div className="min-h-0 flex-1">
              {contribLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading…
                </div>
              ) : contribError ? (
                <div className="text-sm text-red-400">{contribError}</div>
              ) : contribResult && contribResult.rows.length > 0 ? (
                <ObservatoryTable
                  columns={contribResult.columns}
                  rows={contribResult.rows}
                  getRowId={(_, index) => String(index)}
                  maxHeightClassName="max-h-full"
                  enableSorting
                  enableColumnResizing
                  enableColumnPinning
                  monospace
                />
              ) : (
                <div className="text-sm text-muted-foreground">
                  No contributing rows found.
                </div>
              )}
            </div>
          </div>
        </SheetContent>
      </Sheet>

      <div className="p-4 border-b border-border flex items-center justify-between">
        <h4 className="font-medium text-foreground flex items-center gap-2">
          <Database className="w-4 h-4 text-primary" />
          {tableName}
        </h4>
      </div>

      <div className="p-4 space-y-4">
        {/* Transformation SQL */}
        {details.sql && (
          <div>
            <div className="flex items-center gap-2 text-sm text-foreground mb-2 font-medium">
              <Code className="w-4 h-4" />
              Transformation SQL
            </div>
            <Highlight
              theme={themes.vsDark}
              code={cleanSqlForDisplay(details.sql)}
              language="sql"
            >
              {({ style, tokens, getLineProps, getTokenProps }) => (
                <div className="rounded-md border border-border bg-muted/30 overflow-x-auto max-h-64">
                  <pre
                    style={{
                      ...style,
                      margin: 0,
                      backgroundColor: 'transparent',
                    }}
                    className="p-3 text-xs leading-relaxed"
                  >
                    {tokens.map((line, i) => (
                      <div key={i} {...getLineProps({ line })}>
                        {line.map((token, key) => (
                          <span key={key} {...getTokenProps({ token })} />
                        ))}
                      </div>
                    ))}
                  </pre>
                </div>
              )}
            </Highlight>
          </div>
        )}

        {/* Contributing rows (aggregates) / upstream lookup (1:1) */}
        {onQuerySource &&
          details.upstreamAssetKeys &&
          details.upstreamAssetKeys.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm text-foreground mb-2 font-medium">
                <Terminal className="w-4 h-4" />
                Contributing rows
              </div>
              <div className="space-y-2">
                {details.upstreamAssetKeys.map((upstreamAssetKey) => {
                  const upstreamLabel = upstreamAssetKey.split('/').pop()
                  return (
                    <div
                      key={upstreamAssetKey}
                      className="flex items-center justify-between gap-3 rounded-md border border-border bg-muted/20 px-3 py-2"
                    >
                      <div className="text-xs text-foreground">
                        {upstreamLabel}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={() => {
                            setContribUpstreamAssetKey(upstreamAssetKey)
                            setContribOpen(true)
                            setContribPage(0)
                          }}
                        >
                          View rows
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={async () => {
                            const result = await getContributingRowsQuery({
                              data: {
                                downstreamAssetKey: assetKey,
                                upstreamAssetKey,
                                rowData,
                                limit: 100,
                                trinoUrl: settings.connections.trinoUrl,
                                timeoutMs: settings.query.timeoutMs,
                                catalog: settings.defaults.catalog,
                              },
                            })

                            if ('error' in result) {
                              console.error(
                                '[ContributingRows] Error:',
                                result.error,
                              )
                              return
                            }

                            onQuerySource(result.query)
                          }}
                        >
                          Open SQL
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

        {/* Quality Checks */}
        {details.checks && details.checks.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-sm text-foreground mb-2 font-medium">
              <CheckCircle className="w-4 h-4" />
              Quality Checks
            </div>
            <div className="flex flex-wrap gap-2">
              {details.checks.map((check) => (
                <div
                  key={check.name}
                  className="flex items-center gap-2 text-xs bg-muted/30 border border-border px-3 py-1.5 rounded"
                >
                  {check.status === 'PASSED' ? (
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  )}
                  <span className="text-foreground">{check.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Row Data at this Stage */}
        {details.stageData && details.stageData.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-sm text-foreground mb-2 font-medium">
              <Database className="w-4 h-4" />
              {getDataRowMessage().title}{' '}
              <code className="bg-muted px-1.5 py-0.5 rounded text-primary ml-1">
                {tableName}
              </code>
              <span className="text-muted-foreground">
                {getDataRowMessage().subtitle}
              </span>
            </div>
            <ObservatoryTable
              columns={Object.keys(details.stageData[0])}
              rows={details.stageData}
              getRowId={(_, index) => String(index)}
              maxHeightClassName="max-h-64"
              enableSorting
              enableColumnResizing
              enableColumnPinning
              monospace
            />
          </div>
        )}

        {/* No data found */}
        {!details.sql &&
          (!details.checks || details.checks.length === 0) &&
          (!details.stageData || details.stageData.length === 0) && (
            <div className="text-sm text-muted-foreground">
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

export function RowJourney({
  assetKey,
  rowData,
  className = '',
  onQuerySource,
}: RowJourneyProps) {
  const [graphData, setGraphData] = useState<{
    nodes: Array<{ keyPath: string; label: string; computeKind?: string }>
    edges: Array<{ source: string; target: string }>
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Selected node for detail panel
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [nodeDetails, setNodeDetails] = useState<NodeDetails | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
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
  }, [assetKey, settings.connections.dagsterGraphqlUrl])

  // Load details when node is selected
  useEffect(() => {
    if (!selectedNode) {
      setNodeDetails(null)
      return
    }

    async function loadNodeDetails() {
      setDetailsLoading(true)
      try {
        // Fetch asset details and quality checks
        const [assetInfo, qualityInfo] = await Promise.all([
          getAssetDetails({
            data: {
              assetKeyPath: selectedNode!,
              dagsterUrl: settings.connections.dagsterGraphqlUrl,
            },
          }),
          getAssetChecks({
            data: {
              assetKey: selectedNode!.split('/'),
              dagsterUrl: settings.connections.dagsterGraphqlUrl,
            },
          }),
        ])

        const checks =
          'error' in qualityInfo
            ? []
            : qualityInfo.map((check) => ({
                name: check.name,
                status: check.status,
              }))

        const sql =
          'error' in assetInfo ? undefined : extractTransformationSql(assetInfo)

        const upstreamAssetKeys = graphData
          ? graphData.edges
              .filter((e) => e.target === selectedNode)
              .map((e) => e.source)
          : []

        setNodeDetails({
          sql,
          checks,
          stageData: undefined,
          upstreamAssetKeys,
        })
      } catch (err) {
        console.error('Failed to load node details:', err)
        setNodeDetails(null)
      } finally {
        setDetailsLoading(false)
      }
    }

    loadNodeDetails()
  }, [selectedNode, rowData, graphData, settings.connections.dagsterGraphqlUrl])

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
      style: { stroke: 'var(--border)', strokeWidth: 2 },
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
        className={`flex flex-col items-center justify-center h-64 text-muted-foreground ${className}`}
      >
        <Database className="w-8 h-8 mb-2 opacity-50" />
        <p>No lineage data available</p>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Flow visualization */}
      <div className="h-72 bg-background rounded-xl border border-border">
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
          <Controls
            showInteractive={false}
            className="!bg-card !border-border !rounded-none [&>button]:!bg-card [&>button]:!border-border [&>button]:!fill-muted-foreground [&>button:hover]:!bg-muted"
          />
        </ReactFlow>
      </div>

      {/* Detail panel below flow */}
      <NodeDetailPanel
        assetKey={selectedNode || assetKey}
        isLoading={detailsLoading}
        details={nodeDetails}
        rowData={rowData}
        onQuerySource={onQuerySource}
      />
    </div>
  )
}

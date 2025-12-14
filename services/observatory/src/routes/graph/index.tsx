/**
 * Lineage Graph Route
 *
 * Interactive visualization of asset dependencies using React Flow.
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useCallback, useEffect, useState } from 'react'
import { z } from 'zod'

import { AlertCircle, Filter } from 'lucide-react'
import type { GraphNode } from '@/server/graph.server'
import { GraphCanvas, GraphLegend } from '@/components/GraphCanvas'
import { NodeInfoPanel } from '@/components/NodeInfoPanel'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getAssetGraph, getAssetNeighbors } from '@/server/graph.server'

// Search params for focused view
const graphSearchSchema = z.object({
  focus: z.string().optional(),
  depth: z.coerce.number().optional().default(2),
})

export const Route = createFileRoute('/graph/')({
  validateSearch: graphSearchSchema,
  loaderDeps: ({ search }) => ({ focus: search.focus, depth: search.depth }),
  loader: async ({ deps: { focus, depth } }) => {
    if (focus) {
      // Load focused subgraph
      const graph = await getAssetNeighbors({
        data: { assetKey: focus, direction: 'both', depth: depth ?? 2 },
      })
      return { graph, focusedAsset: focus }
    } else {
      // Load full graph
      const graph = await getAssetGraph()
      return { graph, focusedAsset: undefined }
    }
  },
  component: GraphPage,
})

function GraphPage() {
  const { graph, focusedAsset: initialFocus } = Route.useLoaderData()
  const navigate = useNavigate()
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const hasError = 'error' in graph

  // Find selected node in graph data
  const handleAssetSelect = useCallback(
    (keyPath: string) => {
      if (!hasError) {
        const node = graph.nodes.find((n) => n.keyPath === keyPath)
        setSelectedNode(node || null)
      }
    },
    [graph, hasError],
  )

  // Handle focus navigation
  const handleFocusGraph = useCallback(
    (keyPath: string) => {
      navigate({ to: '/graph', search: { focus: keyPath, depth: 2 } })
    },
    [navigate],
  )

  // Clear focus
  const clearFocus = useCallback(() => {
    navigate({ to: '/graph', search: {} })
    setSelectedNode(null)
  }, [navigate])

  // Close info panel
  const handleClosePanel = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // Set initially focused node as selected
  useEffect(() => {
    if (initialFocus && !hasError) {
      const node = graph.nodes.find((n) => n.keyPath === initialFocus)
      setSelectedNode(node || null)
    }
  }, [initialFocus, graph, hasError])

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main Graph Area */}
      <div className="flex-1 flex flex-col">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b bg-card">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">Lineage Graph</h1>
            {initialFocus && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Focused on:
                </span>
                <Badge variant="outline" className="max-w-[40ch] truncate">
                  {initialFocus}
                </Badge>
                <Button variant="link" size="sm" onClick={clearFocus}>
                  Show all
                </Button>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!hasError && (
              <span className="text-sm text-muted-foreground">
                {graph.nodes.length} assets • {graph.edges.length} connections
              </span>
            )}
          </div>
        </div>

        {/* Error State */}
        {hasError ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-8">
              <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">
                Failed to load graph
              </h2>
              <p className="text-muted-foreground mb-4">{graph.error}</p>
              <p className="text-sm text-muted-foreground">
                Make sure Dagster is running at{' '}
                <code className="bg-muted px-1 rounded-none">
                  localhost:3000
                </code>
              </p>
            </div>
          </div>
        ) : graph.nodes.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-8">
              <Filter className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">No assets found</h2>
              <p className="text-muted-foreground">
                {initialFocus
                  ? `No assets found around "${initialFocus}"`
                  : 'No assets are registered in Dagster yet.'}
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Graph Canvas */}
            <div className="flex-1 relative">
              <GraphCanvas
                graphNodes={graph.nodes}
                graphEdges={graph.edges}
                focusedAsset={initialFocus}
                onAssetSelect={handleAssetSelect}
              />

              {/* Legend Overlay */}
              <div className="absolute bottom-4 left-4">
                <GraphLegend />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Side Panel */}
      {selectedNode && (
        <NodeInfoPanel
          node={selectedNode}
          onClose={handleClosePanel}
          onFocusGraph={handleFocusGraph}
        />
      )}
    </div>
  )
}

/**
 * Lineage Graph Route
 *
 * Interactive visualization of asset dependencies using React Flow.
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useCallback, useEffect, useState } from 'react'
import { z } from 'zod'

import { GraphCanvas, GraphLegend } from '@/components/GraphCanvas'
import { NodeInfoPanel } from '@/components/NodeInfoPanel'
import { getAssetGraph, getAssetNeighbors, type GraphNode } from '@/server/graph.server'
import { AlertCircle, Filter } from 'lucide-react'

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
        data: { assetKey: focus, direction: 'both', depth: depth ?? 2 }
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
  const handleAssetSelect = useCallback((keyPath: string) => {
    if (!hasError) {
      const node = graph.nodes.find(n => n.keyPath === keyPath)
      setSelectedNode(node || null)
    }
  }, [graph, hasError])

  // Handle focus navigation
  const handleFocusGraph = useCallback((keyPath: string) => {
    navigate({ to: '/graph', search: { focus: keyPath, depth: 2 } })
  }, [navigate])

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
      const node = graph.nodes.find(n => n.keyPath === initialFocus)
      setSelectedNode(node || null)
    }
  }, [initialFocus, graph, hasError])

  return (
    <div className="flex h-[calc(100vh-0px)] overflow-hidden">
      {/* Main Graph Area */}
      <div className="flex-1 flex flex-col">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-slate-100">Lineage Graph</h1>
            {initialFocus && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Focused on:</span>
                <span className="px-2 py-1 text-sm bg-cyan-600/20 text-cyan-300 rounded">
                  {initialFocus}
                </span>
                <button
                  onClick={clearFocus}
                  className="text-xs text-slate-400 hover:text-slate-300 underline"
                >
                  Show all
                </button>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!hasError && (
              <span className="text-sm text-slate-400">
                {graph.nodes.length} assets • {graph.edges.length} connections
              </span>
            )}
          </div>
        </div>

        {/* Error State */}
        {hasError ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-8">
              <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-100 mb-2">Failed to load graph</h2>
              <p className="text-slate-400 mb-4">{graph.error}</p>
              <p className="text-sm text-slate-500">
                Make sure Dagster is running at{' '}
                <code className="bg-slate-800 px-1 rounded">localhost:10006</code>
              </p>
            </div>
          </div>
        ) : graph.nodes.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center p-8">
              <Filter className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-100 mb-2">No assets found</h2>
              <p className="text-slate-400">
                {initialFocus
                  ? `No assets found around "${initialFocus}"`
                  : 'No assets are registered in Dagster yet.'
                }
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

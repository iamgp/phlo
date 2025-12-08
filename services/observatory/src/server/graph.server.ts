/**
 * Graph Server Functions
 *
 * Server-side functions for building and querying the asset lineage graph.
 * These run only on the server and query Dagster GraphQL for dependency data.
 */

import { createServerFn } from '@tanstack/react-start'

// Types for graph data
export interface GraphNode {
  id: string
  keyPath: string
  key: string[]
  label: string
  description?: string
  computeKind?: string
  groupName?: string
  layer: 'source' | 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'
  lastMaterialization?: string
  upstreamCount: number
  downstreamCount: number
}

export interface GraphEdge {
  source: string
  target: string
}

export interface AssetGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// GraphQL query for asset dependencies
const ASSET_GRAPH_QUERY = `
  query AssetGraphQuery {
    assetsOrError {
      ... on AssetConnection {
        nodes {
          id
          key {
            path
          }
          definition {
            description
            computeKind
            groupName
            dependencyKeys {
              path
            }
            dependedByKeys {
              path
            }
          }
          assetMaterializations(limit: 1) {
            timestamp
          }
        }
      }
      ... on PythonError {
        message
      }
    }
  }
`

/**
 * Determine the data layer based on asset key path
 */
function inferLayer(keyPath: string): GraphNode['layer'] {
  const path = keyPath.toLowerCase()
  if (path.includes('publish') || path.includes('mart') || path.startsWith('mrt_')) {
    return 'publish'
  }
  if (path.includes('gold') || path.startsWith('dim_') || path.startsWith('fct_')) {
    return 'gold'
  }
  if (path.includes('silver') || path.includes('stg_')) {
    return 'silver'
  }
  if (path.includes('bronze') || path.includes('raw')) {
    return 'bronze'
  }
  if (path.startsWith('dlt_') || path.includes('ingest')) {
    return 'source'
  }
  return 'unknown'
}

/**
 * Get the full asset graph with dependencies
 */
export const getAssetGraph = createServerFn().handler(
  async (): Promise<AssetGraph | { error: string }> => {
    const dagsterUrl = process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

    try {
      const response = await fetch(dagsterUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: ASSET_GRAPH_QUERY }),
        signal: AbortSignal.timeout(15000),
      })

      if (!response.ok) {
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const result = await response.json()

      if (result.errors) {
        return { error: result.errors[0]?.message || 'GraphQL error' }
      }

      const { assetsOrError } = result.data

      if (assetsOrError.__typename === 'PythonError') {
        return { error: assetsOrError.message }
      }

      const nodes: GraphNode[] = []
      const edges: GraphEdge[] = []
      const nodeMap = new Map<string, GraphNode>()

      // First pass: create all nodes
      for (const asset of assetsOrError.nodes) {
        const keyPath = asset.key.path.join('/')
        const node: GraphNode = {
          id: asset.id,
          keyPath,
          key: asset.key.path,
          label: asset.key.path[asset.key.path.length - 1] || keyPath,
          description: asset.definition?.description,
          computeKind: asset.definition?.computeKind,
          groupName: asset.definition?.groupName,
          layer: inferLayer(keyPath),
          lastMaterialization: asset.assetMaterializations?.[0]?.timestamp,
          upstreamCount: asset.definition?.dependencyKeys?.length || 0,
          downstreamCount: asset.definition?.dependedByKeys?.length || 0,
        }
        nodes.push(node)
        nodeMap.set(keyPath, node)
      }

      // Second pass: create edges from dependencyKeys
      for (const asset of assetsOrError.nodes) {
        const targetKeyPath = asset.key.path.join('/')
        const dependencies = asset.definition?.dependencyKeys || []

        for (const depKey of dependencies) {
          const sourceKeyPath = depKey.path.join('/')
          // Only add edge if both nodes exist
          if (nodeMap.has(sourceKeyPath) && nodeMap.has(targetKeyPath)) {
            edges.push({
              source: sourceKeyPath,
              target: targetKeyPath,
            })
          }
        }
      }

      return { nodes, edges }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }
)

/**
 * Get neighbors of a specific asset (focused subgraph)
 */
export const getAssetNeighbors = createServerFn()
  .inputValidator((input: { assetKey: string; direction: 'upstream' | 'downstream' | 'both'; depth: number }) => input)
  .handler(
    async ({ data }): Promise<AssetGraph | { error: string }> => {
      // First get the full graph
      const fullGraph = await getAssetGraph()

      if ('error' in fullGraph) {
        return fullGraph
      }

      const { assetKey, direction, depth } = data
      const { nodes, edges } = fullGraph

      // Build adjacency lists
      const upstream = new Map<string, string[]>() // child -> parents
      const downstream = new Map<string, string[]>() // parent -> children

      for (const edge of edges) {
        // upstream: who does this asset depend on?
        if (!upstream.has(edge.target)) upstream.set(edge.target, [])
        upstream.get(edge.target)!.push(edge.source)

        // downstream: who depends on this asset?
        if (!downstream.has(edge.source)) downstream.set(edge.source, [])
        downstream.get(edge.source)!.push(edge.target)
      }

      // BFS to find neighbors within depth
      const includedNodes = new Set<string>([assetKey])

      const bfs = (startKey: string, adjacency: Map<string, string[]>, maxDepth: number) => {
        const queue: [string, number][] = [[startKey, 0]]
        const visited = new Set<string>([startKey])

        while (queue.length > 0) {
          const [current, currentDepth] = queue.shift()!

          if (currentDepth >= maxDepth) continue

          const neighbors = adjacency.get(current) || []
          for (const neighbor of neighbors) {
            if (!visited.has(neighbor)) {
              visited.add(neighbor)
              includedNodes.add(neighbor)
              queue.push([neighbor, currentDepth + 1])
            }
          }
        }
      }

      if (direction === 'upstream' || direction === 'both') {
        bfs(assetKey, upstream, depth)
      }
      if (direction === 'downstream' || direction === 'both') {
        bfs(assetKey, downstream, depth)
      }

      // Filter nodes and edges
      const filteredNodes = nodes.filter(n => includedNodes.has(n.keyPath))
      const filteredEdges = edges.filter(
        e => includedNodes.has(e.source) && includedNodes.has(e.target)
      )

      return { nodes: filteredNodes, edges: filteredEdges }
    }
  )

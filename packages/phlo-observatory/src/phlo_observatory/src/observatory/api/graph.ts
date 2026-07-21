/**
 * Graph Server Functions
 *
 * Thin wrappers that forward graph requests to phlo-api.
 * Keeps Observatory graph logic out of the UI package.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/observatory/api/auth'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

export interface GraphNode {
  id: string
  keyPath: string
  key: Array<string>
  label: string
  description?: string
  computeKind?: string
  groupName?: string
  layer:
    | 'source'
    | 'bronze'
    | 'silver'
    | 'gold'
    | 'marts'
    | 'publish'
    | 'unknown'
  lastMaterialization?: string
  upstreamCount: number
  downstreamCount: number
}

export interface GraphEdge {
  source: string
  target: string
}

export interface AssetGraph {
  nodes: Array<GraphNode>
  edges: Array<GraphEdge>
}

export interface ImpactedAsset {
  keyPath: string
  label: string
  layer: GraphNode['layer']
  depth: number
}

interface ApiGraphNode {
  id: string
  key: Array<string>
  key_path: string
  label: string
  description?: string
  compute_kind?: string
  group_name?: string
  layer: GraphNode['layer']
  last_materialization?: string
  upstream_count: number
  downstream_count: number
}

interface ApiImpactedAsset {
  key_path: string
  label: string
  layer: GraphNode['layer']
  depth: number
}

interface ApiAssetGraph {
  nodes: Array<ApiGraphNode>
  edges: Array<GraphEdge>
}

function transformGraphNode(node: ApiGraphNode): GraphNode {
  return {
    id: node.id,
    key: node.key,
    keyPath: node.key_path,
    label: node.label,
    description: node.description,
    computeKind: node.compute_kind,
    groupName: node.group_name,
    layer: node.layer,
    lastMaterialization: node.last_materialization,
    upstreamCount: node.upstream_count,
    downstreamCount: node.downstream_count,
  }
}

function transformAssetGraph(graph: ApiAssetGraph): AssetGraph {
  return {
    nodes: graph.nodes.map(transformGraphNode),
    edges: graph.edges,
  }
}

function transformImpactedAsset(asset: ApiImpactedAsset): ImpactedAsset {
  return {
    keyPath: asset.key_path,
    label: asset.label,
    layer: asset.layer,
    depth: asset.depth,
  }
}

export async function fetchAssetGraphFromApi(): Promise<
  ApiAssetGraph | { error: string }
> {
  return apiGet<ApiAssetGraph | { error: string }>(
    '/api/observatory/asset-graph',
  )
}

async function fetchAssetNeighborsFromApi(params: {
  assetKey: string
  direction: 'upstream' | 'downstream' | 'both'
  depth: number
}): Promise<ApiAssetGraph | { error: string }> {
  return apiGet<ApiAssetGraph | { error: string }>(
    '/api/observatory/asset-graph/neighbors',
    {
      asset_key: params.assetKey,
      direction: params.direction,
      depth: params.depth,
    },
  )
}

export async function fetchAssetImpactFromApi(params: {
  assetKey: string
  maxDepth?: number
}): Promise<Array<ApiImpactedAsset> | { error: string }> {
  return apiGet<Array<ApiImpactedAsset> | { error: string }>(
    '/api/observatory/asset-graph/impact',
    {
      asset_key: params.assetKey,
      max_depth: params.maxDepth ?? 99,
    },
  )
}

export const getAssetGraph = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: Record<string, never> = {}) => input)
  .handler(async (): Promise<AssetGraph | { error: string }> => {
    try {
      const result = await withCache(
        () => fetchAssetGraphFromApi(),
        cacheKeys.graphFull(),
        cacheTTL.graphFull,
      )
      if ('error' in result) return result
      return transformAssetGraph(result)
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

export const getAssetNeighbors = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      assetKey: string
      direction: 'upstream' | 'downstream' | 'both'
      depth: number
    }) => input,
  )
  .handler(async ({ data }): Promise<AssetGraph | { error: string }> => {
    try {
      const result = await withCache(
        () =>
          fetchAssetNeighborsFromApi({
            assetKey: data.assetKey,
            direction: data.direction,
            depth: data.depth,
          }),
        cacheKeys.graphNeighbors(data.assetKey, data.direction, data.depth),
        cacheTTL.graphNeighbors,
      )
      if ('error' in result) return result
      return transformAssetGraph(result)
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

export const getAssetImpact = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { assetKey: string; maxDepth?: number }) => input)
  .handler(
    async ({ data }): Promise<Array<ImpactedAsset> | { error: string }> => {
      try {
        const result = await fetchAssetImpactFromApi({
          assetKey: data.assetKey,
          maxDepth: data.maxDepth,
        })
        if ('error' in result) return result
        return result.map(transformImpactedAsset)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

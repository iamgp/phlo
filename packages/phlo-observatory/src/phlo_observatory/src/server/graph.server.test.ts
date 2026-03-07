import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiGet = vi.fn()

vi.mock('@/server/phlo-api', () => ({
  apiGet,
}))

describe('graph.server api wrappers', () => {
  beforeEach(() => {
    apiGet.mockReset()
  })

  it('fetches the asset graph from phlo-api', async () => {
    const { fetchAssetGraphFromApi } = await import('@/server/graph.server')
    const payload = { nodes: [], edges: [] }
    apiGet.mockResolvedValue(payload)

    const result = await fetchAssetGraphFromApi({
      dagsterUrl: 'http://dagster:3000/graphql',
    })

    expect(result).toEqual(payload)
    expect(apiGet).toHaveBeenCalledWith('/api/dagster/graph', {
      dagster_url: 'http://dagster:3000/graphql',
    })
  })

  it('fetches impact data from phlo-api', async () => {
    const { fetchAssetImpactFromApi } = await import('@/server/graph.server')
    const payload: Array<{
      key_path: string
      label: string
      layer: 'source'
      depth: number
    }> = []
    apiGet.mockResolvedValue(payload)

    const result = await fetchAssetImpactFromApi({
      assetKey: 'raw.orders',
      maxDepth: 2,
      dagsterUrl: 'http://dagster:3000/graphql',
    })

    expect(result).toEqual(payload)
    expect(apiGet).toHaveBeenCalledWith('/api/dagster/graph/impact', {
      asset_key: 'raw.orders',
      max_depth: 2,
      dagster_url: 'http://dagster:3000/graphql',
    })
  })
})

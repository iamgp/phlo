import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiGet = vi.fn()

vi.mock('@/server/phlo-api', () => ({
  apiGet,
}))

describe('observatory data product resources', () => {
  beforeEach(() => {
    apiGet.mockReset()
  })

  it('fetches Data Product records from phlo-api', async () => {
    apiGet.mockResolvedValue({
      items: [
        {
          id: 'gold.orders',
          name: 'gold.orders',
          classifications: ['internal'],
          publication_state: 'published',
          readiness_state: 'ok',
          kinds: ['table'],
          source_refs: [],
          metadata: {},
        },
      ],
    })

    const { getObservatoryDataProductRecords } = await import('./resources')
    const result = await getObservatoryDataProductRecords()

    expect(result.error).toBeNull()
    expect(result.data).toEqual([
      expect.objectContaining({
        id: 'gold.orders',
        publication_state: 'published',
      }),
    ])
    expect(apiGet).toHaveBeenCalledWith(
      '/api/observatory/data-products',
      undefined,
      8000,
    )
  })
})

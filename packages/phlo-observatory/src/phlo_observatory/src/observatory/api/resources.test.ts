import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiGet = vi.fn()

vi.mock('@/server/phlo-api', () => ({
  apiGet,
}))

describe('observatory dataset resources', () => {
  beforeEach(() => {
    apiGet.mockReset()
  })

  it('fetches Dataset records from phlo-api', async () => {
    apiGet.mockResolvedValue({
      items: [
        {
          id: 'gold.orders',
          name: 'gold.orders',
          classifications: ['internal'],
          publication_state: 'published',
          readiness_state: 'ok',
          candidate: false,
          kinds: ['table'],
          source_refs: [],
          metadata: {},
        },
      ],
    })

    const { getObservatoryDatasetRecords } = await import('./resources')
    const result = await getObservatoryDatasetRecords()

    expect(result.error).toBeNull()
    expect(result.data).toEqual([
      expect.objectContaining({
        id: 'gold.orders',
        publication_state: 'published',
      }),
    ])
    expect(apiGet).toHaveBeenCalledWith(
      '/api/observatory/datasets',
      undefined,
      8000,
    )
  })
})

import { describe, expect, test } from 'vitest'

import {
  invalidateCachedResource,
  invalidateCachedResources,
  loadCachedResource,
} from './liveResource'

describe('liveResource cache invalidation', () => {
  test('invalidates one cached resource key', async () => {
    const key = 'test:single-invalidate'
    let calls = 0
    const load = () => {
      calls += 1
      return Promise.resolve({ data: [calls], error: null })
    }

    await loadCachedResource(key, load, { staleMs: 60_000 })
    await loadCachedResource(key, load, { staleMs: 60_000 })
    expect(calls).toBe(1)

    invalidateCachedResource(key)
    const refreshed = await loadCachedResource(key, load, { staleMs: 60_000 })

    expect(calls).toBe(2)
    expect(refreshed.data).toEqual([2])
  })

  test('invalidates several cached resource keys', async () => {
    const firstKey = 'test:multi-invalidate:first'
    const secondKey = 'test:multi-invalidate:second'
    let firstCalls = 0
    let secondCalls = 0

    await loadCachedResource(firstKey, () => {
      firstCalls += 1
      return Promise.resolve({ data: [firstCalls], error: null })
    })
    await loadCachedResource(secondKey, () => {
      secondCalls += 1
      return Promise.resolve({ data: [secondCalls], error: null })
    })

    invalidateCachedResources([firstKey, secondKey])

    await loadCachedResource(firstKey, () => {
      firstCalls += 1
      return Promise.resolve({ data: [firstCalls], error: null })
    })
    await loadCachedResource(secondKey, () => {
      secondCalls += 1
      return Promise.resolve({ data: [secondCalls], error: null })
    })

    expect(firstCalls).toBe(2)
    expect(secondCalls).toBe(2)
  })
})

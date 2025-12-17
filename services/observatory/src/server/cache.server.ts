/**
 * Cache stats endpoint - see ADR 0019-observatory-metadata-caching.md
 */

import { createServerFn } from '@tanstack/react-start'

import { clearCache, getCacheStats, invalidateCache } from './cache'

export const getCacheStatsEndpoint = createServerFn().handler(() => {
  return Promise.resolve(getCacheStats())
})

export const invalidateCacheEndpoint = createServerFn()
  .inputValidator((input: { pattern: string }) => input)
  .handler(({ data: { pattern } }) => {
    const count = invalidateCache(pattern)
    return Promise.resolve({ invalidated: count })
  })

export const clearCacheEndpoint = createServerFn().handler(() => {
  clearCache()
  return Promise.resolve({ cleared: true })
})

import { useEffect, useMemo, useState } from 'react'

import type { V2ResourceResult } from '@/v2/api/types'

type CachedEntry<T> = {
  expiresAt: number
  promise: Promise<V2ResourceResult<T>> | null
  result: V2ResourceResult<T>
}

const resourceCache = new Map<string, CachedEntry<unknown>>()
const resourceKeys = new WeakMap<object, string>()
const cacheVersion = '2026-05-01-product-workflow-cache'
let nextResourceKey = 0

export function useLiveResource<T>(
  load: () => Promise<V2ResourceResult<Array<T>>>,
  intervalMs = 60_000,
  cacheKey?: string,
) {
  const key = useMemo(
    () => cacheKey ?? stableResourceKey(load),
    [cacheKey, load],
  )
  const [result, setResult] = useState<V2ResourceResult<Array<T>>>(
    () => readCachedResource<Array<T>>(key) ?? { data: null, error: null },
  )

  useEffect(() => {
    let cancelled = false

    async function refresh(force = false) {
      const next = await loadCachedResource<Array<T>>(key, load, {
        force,
        staleMs: intervalMs,
      })
      if (!cancelled) setResult(next)
    }

    void refresh()
    const interval = window.setInterval(() => {
      void refresh(true)
    }, intervalMs)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [intervalMs, key, load])

  return result
}

export function readCachedResource<T>(key: string): V2ResourceResult<T> | null {
  const versionedKey = `${cacheVersion}:${key}`
  const cached = resourceCache.get(versionedKey) as CachedEntry<T> | undefined
  return cached?.result ?? null
}

export async function loadCachedResource<T>(
  key: string,
  load: () => Promise<V2ResourceResult<T>>,
  {
    force = false,
    staleMs = 60_000,
  }: {
    force?: boolean
    staleMs?: number
  } = {},
): Promise<V2ResourceResult<T>> {
  const versionedKey = `${cacheVersion}:${key}`
  const cached = resourceCache.get(versionedKey) as CachedEntry<T> | undefined
  const now = Date.now()

  if (!force && cached?.result && cached.expiresAt > now) {
    return cached.result
  }
  if (cached?.promise) return cached.promise

  const promise = load().then((result) => {
    if (isCacheableResult(result)) {
      resourceCache.set(versionedKey, {
        expiresAt: Date.now() + staleMs,
        promise: null,
        result,
      })
    } else if (cached?.result) {
      resourceCache.set(versionedKey, {
        expiresAt: Date.now(),
        promise: null,
        result: cached.result,
      })
    } else {
      resourceCache.delete(versionedKey)
    }
    return result
  })

  resourceCache.set(versionedKey, {
    expiresAt: cached?.expiresAt ?? 0,
    promise,
    result: cached?.result ?? { data: null, error: null },
  })

  return promise
}

function isCacheableResult<T>(result: V2ResourceResult<T>): boolean {
  if (result.error) return false
  return hasUsefulData(result.data)
}

function hasUsefulData(data: unknown): boolean {
  if (data === null || data === undefined) return false
  if (Array.isArray(data)) return true
  if (typeof data !== 'object') return true

  if ('health' in data && 'counters' in data) {
    return true
  }

  if ('items' in data && Array.isArray(data.items)) return true
  if ('pages' in data && Array.isArray(data.pages)) return data.pages.length > 0
  if ('columns' in data && Array.isArray(data.columns)) return true
  if ('rows' in data && Array.isArray(data.rows)) return true

  return true
}

function stableResourceKey(load: object): string {
  const existing = resourceKeys.get(load)
  if (existing) return existing
  const key = `resource:${nextResourceKey}`
  nextResourceKey += 1
  resourceKeys.set(load, key)
  return key
}

export function readMetric(
  metadata: Record<string, unknown>,
  key: string,
): string | number | null {
  const value = metadata[key]
  if (typeof value === 'string' || typeof value === 'number') {
    return value
  }
  return null
}

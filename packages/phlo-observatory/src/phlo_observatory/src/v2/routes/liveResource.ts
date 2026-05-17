import { useEffect, useMemo, useState } from 'react'

import type { V2ResourceResult } from '@/v2/api/types'

declare global {
  interface Window {
    __PHLO_API_BROWSER_URL__?: string
  }
}

type CachedEntry<T> = {
  expiresAt: number
  promise: Promise<V2ResourceResult<T>> | null
  result: V2ResourceResult<T>
}

const resourceCache = new Map<string, CachedEntry<unknown>>()
const resourceKeys = new WeakMap<object, string>()
const cacheVersion = '2026-05-17-core-logs-cache'
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

    void refresh(true)
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

function readCachedResource<T>(key: string): V2ResourceResult<T> | null {
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

  const promise = load().then(async (result) => {
    const fallback = await browserFallbackResource<T>(key)
    const loaded = isCacheableResult(fallback) ? fallback : result

    return Promise.resolve(loaded).then((nextResult) => {
      if (isCacheableResult(nextResult)) {
        resourceCache.set(versionedKey, {
          expiresAt: Date.now() + staleMs,
          promise: null,
          result: nextResult,
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
      return nextResult
    })
  })

  resourceCache.set(versionedKey, {
    expiresAt: cached?.expiresAt ?? 0,
    promise,
    result: cached?.result ?? { data: null, error: null },
  })

  return promise
}

async function browserFallbackResource<T>(
  key: string,
): Promise<V2ResourceResult<T>> {
  if (typeof window === 'undefined') return { data: null, error: null }
  const base = window.__PHLO_API_BROWSER_URL__
  const endpoint = fallbackEndpoint(key)
  if (!base || !endpoint) return { data: null, error: null }

  try {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 8000)
    const response = await fetch(`${base}${endpoint}`, {
      signal: controller.signal,
    })
    window.clearTimeout(timeout)
    if (!response.ok) {
      return {
        data: null,
        error: `phlo-api error: ${response.status} ${response.statusText}`,
      }
    }
    const payload = await response.json()
    return {
      data: normalizeFallbackPayload<T>(key, payload),
      error: null,
    }
  } catch (error) {
    return {
      data: null,
      error:
        error instanceof Error ? error.message : 'Lakehouse API is unavailable',
    }
  }
}

function fallbackEndpoint(key: string): string | null {
  const prefix = '/api/observatory/v2'
  const endpoints: Record<string, string> = {
    'v2:overview': `${prefix}/overview`,
    'v2:capabilities': `${prefix}/capabilities`,
    'v2:services': `${prefix}/services`,
    'v2:operations': `${prefix}/operations`,
    'v2:runs': `${prefix}/runs`,
    'v2:storage': `${prefix}/storage`,
    'v2:observability': `${prefix}/observability`,
    'v2:governance': `${prefix}/governance`,
    'v2:catalog': `${prefix}/catalog`,
    'v2:apis': `${prefix}/apis`,
    'v2:bi': `${prefix}/bi`,
    'v2:assets': `${prefix}/assets`,
    'v2:tables': `${prefix}/tables`,
    'v2:saved-queries': `${prefix}/saved-queries`,
    'v2:quality': `${prefix}/quality`,
    'v2:logs': `${prefix}/logs`,
    'v2:branches': `${prefix}/branches`,
    'v2:extensions': `${prefix}/extensions`,
    'v2:workflow-wizard': `${prefix}/workflow-wizard`,
  }
  return endpoints[key] ?? null
}

function normalizeFallbackPayload<T>(key: string, payload: unknown): T {
  if (
    key === 'v2:branches' &&
    isRecord(payload) &&
    Array.isArray(payload.items)
  ) {
    return payload.items.map((branch) => normalizeBranchFallback(branch)) as T
  }

  if (isRecord(payload) && Array.isArray(payload.items)) {
    return payload.items as T
  }

  return payload as T
}

function normalizeBranchFallback(value: unknown): Record<string, unknown> {
  const branch = isRecord(value) ? value : {}
  const id = safeString(branch.id) ?? safeString(branch.name) ?? 'branch'
  const name = safeString(branch.name) ?? id
  const current = branch.current === true
  return {
    id,
    name,
    kind: 'branch',
    status: current ? 'current' : 'branch',
    summary: current ? 'Current branch' : 'Branch',
    metadata: isRecord(branch.metadata) ? branch.metadata : {},
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function safeString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

export function invalidateCachedResource(key: string): void {
  resourceCache.delete(`${cacheVersion}:${key}`)
}

export function invalidateCachedResources(keys: Array<string>): void {
  for (const key of keys) {
    invalidateCachedResource(key)
  }
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

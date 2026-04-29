import { useEffect, useState } from 'react'

import type { V2ResourceResult } from '@/v2/api/types'

export function useLiveResource<T>(
  load: () => Promise<V2ResourceResult<Array<T>>>,
  intervalMs = 15_000,
) {
  const [result, setResult] = useState<V2ResourceResult<Array<T>>>({
    data: null,
    error: null,
  })

  useEffect(() => {
    let cancelled = false

    async function refresh() {
      const next = await load()
      if (!cancelled) setResult(next)
    }

    void refresh()
    const interval = window.setInterval(refresh, intervalMs)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [intervalMs, load])

  return result
}

export function readMetric(
  metadata: Record<string, unknown>,
  key: string,
): string | number | boolean | null {
  const value = metadata[key]
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return value
  }
  return null
}

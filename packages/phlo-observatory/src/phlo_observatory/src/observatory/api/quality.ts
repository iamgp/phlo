/**
 * Quality Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import type { MetadataValue, QualityCheck } from '@/server/quality.types'
import { authMiddleware } from '@/observatory/api/auth'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

export type { QualityCheck } from '@/server/quality.types'

// Python API types (snake_case)
interface ApiQualityCheck {
  id?: string
  name: string
  asset_id: string
  description?: string
  severity?: string | null
  status: 'passing' | 'failing' | 'warning' | 'unknown'
  metadata?: Record<string, MetadataValue>
}

interface ApiAssetDetail {
  quality: Array<ApiQualityCheck>
}

function transformStatus(
  status: ApiQualityCheck['status'],
): QualityCheck['status'] {
  if (status === 'passing') return 'PASSED'
  if (status === 'failing' || status === 'warning') return 'FAILED'
  return 'SKIPPED'
}

function transformCheck(c: ApiQualityCheck): QualityCheck {
  const status = transformStatus(c.status)
  return {
    name: c.name,
    assetKey: c.asset_id.split(/[./]/).filter(Boolean),
    description: c.description,
    severity: c.severity === 'WARN' ? 'WARN' : 'ERROR',
    status,
    lastResult: {
      passed: status === 'PASSED',
      metadata: c.metadata,
    },
  }
}

/**
 * Get quality checks for a specific asset
 */
export const getAssetChecks = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { assetKey: Array<string>; dagsterUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { assetKey },
    }): Promise<Array<QualityCheck> | { error: string }> => {
      try {
        const keyPath = assetKey.join('/')
        const result = await withCache(
          () =>
            apiGet<ApiAssetDetail | { error: string }>(
              `/api/observatory/assets/${keyPath}`,
            ),
          cacheKeys.qualityAssetChecks(keyPath),
          cacheTTL.qualityAssetChecks,
        )
        if ('error' in result) return result
        return result.quality.map(transformCheck)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

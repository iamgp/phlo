/**
 * Quality Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import type { MetadataValue, QualityCheck } from './quality.types'
import { authMiddleware } from '@/server/auth.server'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

export type { QualityCheck } from './quality.types'

// Python API types (snake_case)
interface ApiQualityCheck {
  name: string
  asset_key: Array<string>
  description?: string
  severity: 'WARN' | 'ERROR'
  status: 'PASSED' | 'FAILED' | 'IN_PROGRESS' | 'SKIPPED'
  last_execution_time?: string
  last_result?: { passed: boolean; metadata?: Record<string, MetadataValue> }
}

function transformCheck(c: ApiQualityCheck): QualityCheck {
  return {
    name: c.name,
    assetKey: c.asset_key,
    description: c.description,
    severity: c.severity,
    status: c.status,
    lastExecutionTime: c.last_execution_time,
    lastResult: c.last_result,
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
            apiGet<Array<ApiQualityCheck> | { error: string }>(
              `/api/quality/assets/${keyPath}/checks`,
            ),
          cacheKeys.qualityAssetChecks(keyPath),
          cacheTTL.qualityAssetChecks,
        )
        if ('error' in result) return result
        return result.map(transformCheck)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

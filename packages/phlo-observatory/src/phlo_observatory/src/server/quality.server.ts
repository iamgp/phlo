/**
 * Quality Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import type {
  CheckExecution,
  MetadataValue,
  QualityCheck,
  QualityOverview,
  RecentCheckExecution,
} from './quality.types'
import { authMiddleware } from '@/server/auth.server'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

export type {
  CheckExecution,
  QualityCheck,
  QualityOverview,
  RecentCheckExecution,
} from './quality.types'

// Python API types (snake_case)
interface ApiQualityOverview {
  total_checks: number
  passing_checks: number
  failing_checks: number
  warning_checks: number
  quality_score: number
  by_category: Array<{
    category: string
    passing: number
    total: number
    percentage: number
  }>
  trend: Array<{ date: string; score: number }>
}

interface ApiQualityCheck {
  name: string
  asset_key: Array<string>
  description?: string
  severity: 'WARN' | 'ERROR'
  status: 'PASSED' | 'FAILED' | 'IN_PROGRESS' | 'SKIPPED'
  last_execution_time?: string
  last_result?: { passed: boolean; metadata?: Record<string, MetadataValue> }
}

interface ApiCheckExecution {
  timestamp: string
  passed: boolean
  run_id?: string
  metadata?: Record<string, MetadataValue>
}

// Transform functions
function transformOverview(o: ApiQualityOverview): QualityOverview {
  return {
    totalChecks: o.total_checks,
    passingChecks: o.passing_checks,
    failingChecks: o.failing_checks,
    warningChecks: o.warning_checks,
    qualityScore: o.quality_score,
    byCategory: o.by_category,
    trend: o.trend,
  }
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

function transformExecution(e: ApiCheckExecution): CheckExecution {
  return {
    timestamp: e.timestamp,
    passed: e.passed,
    runId: e.run_id,
    metadata: e.metadata,
  }
}

/**
 * Get overview of all quality metrics
 */
export const getQualityOverview = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { dagsterUrl?: string } = {}) => input)
  .handler(async (): Promise<QualityOverview | { error: string }> => {
    try {
      const result = await withCache(
        () =>
          apiGet<ApiQualityOverview | { error: string }>(
            '/api/quality/overview',
          ),
        cacheKeys.qualityOverview(),
        cacheTTL.qualityOverview,
      )
      if ('error' in result) return result
      return transformOverview(result)
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

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

/**
 * Get execution history for a specific check
 */
export const getCheckHistory = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      assetKey: Array<string>
      checkName: string
      limit?: number
      dagsterUrl?: string
    }) => input,
  )
  .handler(
    async ({
      data: { assetKey, checkName, limit = 20 },
    }): Promise<Array<CheckExecution> | { error: string }> => {
      try {
        const keyPath = assetKey.join('/')
        const result = await withCache(
          () =>
            apiGet<Array<ApiCheckExecution> | { error: string }>(
              `/api/quality/assets/${keyPath}/checks/${encodeURIComponent(
                checkName,
              )}/history`,
              { limit },
            ),
          cacheKeys.qualityCheckHistory(keyPath, checkName, limit),
          cacheTTL.qualityCheckHistory,
        )
        if ('error' in result) return result
        return result.map(transformExecution)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get all currently failing checks
 */
export const getFailingChecks = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { dagsterUrl?: string } = {}) => input)
  .handler(async (): Promise<Array<QualityCheck> | { error: string }> => {
    try {
      const result = await withCache(
        () =>
          apiGet<Array<ApiQualityCheck> | { error: string }>(
            '/api/quality/failing',
          ),
        cacheKeys.qualityFailing(),
        cacheTTL.qualityFailing,
      )
      if ('error' in result) return result
      return result.map(transformCheck)
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

/**
 * Get quality dashboard (overview + failing + recent)
 */
export const getQualityDashboard = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { dagsterUrl?: string } = {}) => input)
  .handler(
    async (): Promise<
      | {
          overview: QualityOverview
          failingChecks: Array<QualityCheck>
          recentExecutions: Array<RecentCheckExecution>
          checks: Array<QualityCheck>
        }
      | { error: string }
    > => {
      try {
        const cached = await withCache(
          async () => {
            const [overviewResult, failingResult] = await Promise.all([
              apiGet<ApiQualityOverview | { error: string }>(
                '/api/quality/overview',
              ),
              apiGet<Array<ApiQualityCheck> | { error: string }>(
                '/api/quality/failing',
              ),
            ])

            if ('error' in overviewResult) return overviewResult
            if ('error' in failingResult) return failingResult

            return {
              overview: transformOverview(overviewResult),
              failingChecks: failingResult.map(transformCheck),
              recentExecutions: [],
              checks: failingResult.map(transformCheck),
            }
          },
          cacheKeys.qualityDashboard(),
          cacheTTL.qualityDashboard,
        )

        return cached
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

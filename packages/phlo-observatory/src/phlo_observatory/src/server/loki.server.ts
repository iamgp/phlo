/**
 * Loki Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

// Types
export interface LogEntry {
  timestamp: Date
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  metadata: Record<string, string>
}

export interface LogQueryResult {
  entries: Array<LogEntry>
  hasMore: boolean
}

export interface LokiConnectionStatus {
  connected: boolean
  error?: string
  version?: string
}

// Python API types (snake_case)
interface ApiLogEntry {
  timestamp: string
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  metadata: Record<string, string>
}

interface ApiLogQueryResult {
  entries: Array<ApiLogEntry>
  has_more: boolean
}

// Transform
function transformLogEntry(e: ApiLogEntry): LogEntry {
  return {
    timestamp: new Date(e.timestamp),
    level: e.level,
    message: e.message,
    metadata: e.metadata,
  }
}

function buildQueryKey(
  parts: Record<string, string | number | undefined>,
): string {
  return Object.entries(parts)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => `${key}=${value}`)
    .join('&')
}

/**
 * Check if Loki is reachable
 */
export const checkLokiConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { lokiUrl?: string } = {}) => input)
  .handler(async ({ data }): Promise<LokiConnectionStatus> => {
    try {
      const key = cacheKeys.lokiConnection(data.lokiUrl ?? 'default')
      return await withCache(
        () => apiGet<LokiConnectionStatus>('/api/loki/connection'),
        key,
        cacheTTL.lokiLabels,
      )
    } catch (error) {
      return {
        connected: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Query logs with filters
 */
export const queryLogs = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      runId?: string
      assetKey?: string
      job?: string
      partitionKey?: string
      checkName?: string
      level?: 'debug' | 'info' | 'warn' | 'error'
      service?: string
      start: string
      end: string
      limit?: number
      lokiUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(async ({ data }): Promise<LogQueryResult | { error: string }> => {
    try {
      const queryKey = buildQueryKey({
        start: data.start,
        end: data.end,
        runId: data.runId,
        assetKey: data.assetKey,
        job: data.job,
        partitionKey: data.partitionKey,
        checkName: data.checkName,
        level: data.level,
        service: data.service,
        limit: data.limit,
      })
      const key = cacheKeys.lokiQuery(data.lokiUrl ?? 'default', queryKey)
      const result = await withCache(
        () =>
          apiGet<ApiLogQueryResult | { error: string }>('/api/loki/query', {
            start: data.start,
            end: data.end,
            run_id: data.runId,
            asset_key: data.assetKey,
            job: data.job,
            partition_key: data.partitionKey,
            check_name: data.checkName,
            level: data.level,
            service: data.service,
            limit: data.limit,
          }),
        key,
        cacheTTL.lokiQuery,
      )

      if ('error' in result) return result
      return {
        entries: result.entries.map(transformLogEntry),
        hasMore: result.has_more,
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

/**
 * Query logs for a specific Dagster run
 */
export const queryRunLogs = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      runId: string
      level?: 'debug' | 'info' | 'warn' | 'error'
      limit?: number
      lokiUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(async ({ data }): Promise<LogQueryResult | { error: string }> => {
    try {
      const queryKey = buildQueryKey({
        runId: data.runId,
        level: data.level,
        limit: data.limit ?? 500,
      })
      const key = cacheKeys.lokiQuery(data.lokiUrl ?? 'default', queryKey)
      const result = await withCache(
        () =>
          apiGet<ApiLogQueryResult | { error: string }>(
            `/api/loki/runs/${encodeURIComponent(data.runId)}`,
            { level: data.level, limit: data.limit ?? 500 },
          ),
        key,
        cacheTTL.lokiQuery,
      )

      if ('error' in result) return result
      return {
        entries: result.entries.map(transformLogEntry),
        hasMore: result.has_more,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Query logs for a specific asset
 */
export const queryAssetLogs = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      assetKey: string
      partitionKey?: string
      level?: 'debug' | 'info' | 'warn' | 'error'
      hoursBack?: number
      limit?: number
      lokiUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(async ({ data }): Promise<LogQueryResult | { error: string }> => {
    try {
      const queryKey = buildQueryKey({
        assetKey: data.assetKey,
        partitionKey: data.partitionKey,
        level: data.level,
        hoursBack: data.hoursBack ?? 24,
        limit: data.limit ?? 200,
      })
      const key = cacheKeys.lokiQuery(data.lokiUrl ?? 'default', queryKey)
      const result = await withCache(
        () =>
          apiGet<ApiLogQueryResult | { error: string }>(
            `/api/loki/assets/${encodeURIComponent(data.assetKey)}`,
            {
              partition_key: data.partitionKey,
              level: data.level,
              hours_back: data.hoursBack ?? 24,
              limit: data.limit ?? 200,
            },
          ),
        key,
        cacheTTL.lokiQuery,
      )

      if ('error' in result) return result
      return {
        entries: result.entries.map(transformLogEntry),
        hasMore: result.has_more,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Get available log labels
 */
export const getLogLabels = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { lokiUrl?: string } = {}) => input)
  .handler(
    async ({
      data,
    }): Promise<{ labels: Array<string> } | { error: string }> => {
      try {
        const key = cacheKeys.lokiLabels(data.lokiUrl ?? 'default')
        return await withCache(
          () =>
            apiGet<{ labels: Array<string> } | { error: string }>(
              '/api/loki/labels',
            ),
          key,
          cacheTTL.lokiLabels,
        )
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

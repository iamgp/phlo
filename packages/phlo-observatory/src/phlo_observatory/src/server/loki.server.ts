/**
 * Loki Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
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

/**
 * Check if Loki is reachable
 */
export const checkLokiConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { lokiUrl?: string } = {}) => input)
  .handler(async (): Promise<LokiConnectionStatus> => {
    try {
      return await apiGet<LokiConnectionStatus>('/api/loki/connection')
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
  .handler(
    async ({ data }): Promise<LogQueryResult | { error: string }> => {
      try {
        const result = await apiGet<ApiLogQueryResult | { error: string }>(
          '/api/loki/query',
          {
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
          },
        )

        if ('error' in result) return result
        return {
          entries: result.entries.map(transformLogEntry),
          hasMore: result.has_more,
        }
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

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
  .handler(
    async ({
      data: { runId, level, limit = 500 },
    }): Promise<LogQueryResult | { error: string }> => {
      try {
        const result = await apiGet<ApiLogQueryResult | { error: string }>(
          `/api/loki/runs/${encodeURIComponent(runId)}`,
          { level, limit },
        )

        if ('error' in result) return result
        return {
          entries: result.entries.map(transformLogEntry),
          hasMore: result.has_more,
        }
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

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
  .handler(
    async ({
      data: { assetKey, partitionKey, level, hoursBack = 24, limit = 200 },
    }): Promise<LogQueryResult | { error: string }> => {
      try {
        const result = await apiGet<ApiLogQueryResult | { error: string }>(
          `/api/loki/assets/${assetKey}`,
          {
            partition_key: partitionKey,
            level,
            hours_back: hoursBack,
            limit,
          },
        )

        if ('error' in result) return result
        return {
          entries: result.entries.map(transformLogEntry),
          hasMore: result.has_more,
        }
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

/**
 * Get available log labels
 */
export const getLogLabels = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { lokiUrl?: string } = {}) => input)
  .handler(
    async (): Promise<{ labels: Array<string> } | { error: string }> => {
      try {
        return await apiGet<{ labels: Array<string> } | { error: string }>('/api/loki/labels')
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

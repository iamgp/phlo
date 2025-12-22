/**
 * Loki Log Querying Server Functions
 *
 * Server-side functions for querying logs from Loki.
 * Supports correlation by run_id, asset_key, job_name, and partition_key.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { withTiming } from '@/server/logger.server'

// Types for Loki responses
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

interface LokiStream {
  stream: Record<string, string>
  values: Array<[string, string]>
}

interface LokiQueryResponse {
  status: string
  data: {
    resultType: string
    result: Array<LokiStream>
  }
}

const DEFAULT_LOKI_URL = 'http://localhost:3100'

function resolveLokiUrl(override?: string): string {
  if (override && override.trim()) return override
  return process.env.LOKI_URL || DEFAULT_LOKI_URL
}

/**
 * Build a LogQL query with optional filters
 */
function buildLogQuery(filters: {
  runId?: string
  assetKey?: string
  job?: string
  partitionKey?: string
  checkName?: string
  level?: 'debug' | 'info' | 'warn' | 'error'
  service?: string
}): string {
  const labelMatchers: Array<string> = []
  const jsonFilters: Array<string> = []

  // Service filter (container name) - required by Loki to have at least one matcher
  // Docker Compose names containers as: {project}-{service}-{replica}
  // So we use regex to match any container containing the service name
  if (filters.service) {
    labelMatchers.push(`container=~".*${filters.service}.*"`)
  } else {
    // Use a catch-all pattern that matches any non-empty container name
    labelMatchers.push('container=~".+"')
  }

  // Primary correlation fields from JSON logs
  if (filters.runId) {
    jsonFilters.push(`run_id="${filters.runId}"`)
  }
  if (filters.assetKey) {
    jsonFilters.push(`asset_key="${filters.assetKey}"`)
  }
  if (filters.job) {
    jsonFilters.push(`job_name="${filters.job}"`)
  }
  if (filters.partitionKey) {
    jsonFilters.push(`partition_key="${filters.partitionKey}"`)
  }
  if (filters.checkName) {
    jsonFilters.push(`check_name="${filters.checkName}"`)
  }
  if (filters.level) {
    jsonFilters.push(`level="${filters.level}"`)
  }

  // Build LogQL query
  const labelSelector = labelMatchers.join(', ')
  const jsonPipeline =
    jsonFilters.length > 0 ? ` | json | ${jsonFilters.join(' | ')}` : ' | json'

  return `{${labelSelector}}${jsonPipeline}`
}

/**
 * Parse Loki response into LogEntry array
 */
function parseLokiResponse(response: LokiQueryResponse): Array<LogEntry> {
  const entries: Array<LogEntry> = []

  for (const stream of response.data.result) {
    for (const [timestampNs, line] of stream.values) {
      try {
        const parsed = JSON.parse(line)
        entries.push({
          timestamp: new Date(Number(timestampNs) / 1_000_000),
          level: parsed.level || 'info',
          message: parsed.msg || parsed.message || line,
          metadata: {
            ...(parsed.run_id && { run_id: parsed.run_id }),
            ...(parsed.asset_key && { asset_key: parsed.asset_key }),
            ...(parsed.job_name && { job_name: parsed.job_name }),
            ...(parsed.partition_key && {
              partition_key: parsed.partition_key,
            }),
            ...(parsed.fn && { fn: parsed.fn }),
            ...(parsed.durationMs && { durationMs: String(parsed.durationMs) }),
          },
        })
      } catch {
        // Non-JSON log line - include as plain text
        entries.push({
          timestamp: new Date(Number(timestampNs) / 1_000_000),
          level: 'info',
          message: line,
          metadata: stream.stream,
        })
      }
    }
  }

  // Sort by timestamp descending (most recent first)
  entries.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())

  return entries
}

/**
 * Execute a LogQL query against Loki
 */
async function executeLokiQuery(
  query: string,
  start: Date,
  end: Date,
  limit: number = 100,
  options?: { lokiUrl?: string; timeoutMs?: number },
): Promise<LokiQueryResponse> {
  const lokiUrl = resolveLokiUrl(options?.lokiUrl)
  const timeoutMs = options?.timeoutMs ?? 10_000

  return withTiming(
    'executeLokiQuery',
    async () => {
      const params = new URLSearchParams({
        query,
        start: (start.getTime() * 1_000_000).toString(),
        end: (end.getTime() * 1_000_000).toString(),
        limit: limit.toString(),
        direction: 'backward',
      })

      const response = await fetch(
        `${lokiUrl}/loki/api/v1/query_range?${params}`,
        {
          headers: {
            Accept: 'application/json',
          },
          signal: AbortSignal.timeout(timeoutMs),
        },
      )

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Loki error: ${errorText}`)
      }

      return await response.json()
    },
    { query: query.substring(0, 100) },
  )
}

/**
 * Check if Loki is reachable
 */
export const checkLokiConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { lokiUrl?: string } = {}) => input)
  .handler(async ({ data }): Promise<LokiConnectionStatus> => {
    const lokiUrl = resolveLokiUrl(data.lokiUrl)

    try {
      const response = await fetch(`${lokiUrl}/ready`, {
        signal: AbortSignal.timeout(5000),
      })

      if (!response.ok) {
        return {
          connected: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      // Get version info
      const buildResponse = await fetch(
        `${lokiUrl}/loki/api/v1/status/buildinfo`,
        {
          signal: AbortSignal.timeout(5000),
        },
      )

      let version = 'unknown'
      if (buildResponse.ok) {
        const buildInfo = await buildResponse.json()
        version = buildInfo.version || 'unknown'
      }

      return {
        connected: true,
        version,
      }
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
    async ({
      data: {
        runId,
        assetKey,
        job,
        partitionKey,
        checkName,
        level,
        service,
        start,
        end,
        limit = 100,
        lokiUrl,
        timeoutMs,
      },
    }): Promise<LogQueryResult | { error: string }> => {
      try {
        const query = buildLogQuery({
          runId,
          assetKey,
          job,
          partitionKey,
          checkName,
          level,
          service,
        })

        const response = await executeLokiQuery(
          query,
          new Date(start),
          new Date(end),
          limit,
          {
            lokiUrl,
            timeoutMs,
          },
        )

        const entries = parseLokiResponse(response)

        return {
          entries,
          hasMore: entries.length === limit,
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
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
      data: { runId, level, limit = 500, lokiUrl, timeoutMs },
    }): Promise<LogQueryResult | { error: string }> => {
      try {
        const query = buildLogQuery({ runId, level })

        // Query last 24 hours for run logs
        const end = new Date()
        const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)

        const response = await executeLokiQuery(query, start, end, limit, {
          lokiUrl,
          timeoutMs,
        })

        const entries = parseLokiResponse(response)

        return {
          entries,
          hasMore: entries.length === limit,
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
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
      data: {
        assetKey,
        partitionKey,
        level,
        hoursBack = 24,
        limit = 200,
        lokiUrl,
        timeoutMs,
      },
    }): Promise<LogQueryResult | { error: string }> => {
      try {
        const query = buildLogQuery({ assetKey, partitionKey, level })

        const end = new Date()
        const start = new Date(end.getTime() - hoursBack * 60 * 60 * 1000)

        const response = await executeLokiQuery(query, start, end, limit, {
          lokiUrl,
          timeoutMs,
        })

        const entries = parseLokiResponse(response)

        return {
          entries,
          hasMore: entries.length === limit,
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get available log labels (for autocomplete/filtering)
 */
export const getLogLabels = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { lokiUrl?: string } = {}) => input)
  .handler(
    async ({
      data,
    }): Promise<{ labels: Array<string> } | { error: string }> => {
      const lokiUrl = resolveLokiUrl(data.lokiUrl)

      try {
        const response = await fetch(`${lokiUrl}/loki/api/v1/labels`, {
          headers: {
            Accept: 'application/json',
          },
          signal: AbortSignal.timeout(5000),
        })

        if (!response.ok) {
          const errorText = await response.text()
          return { error: `Loki error: ${errorText}` }
        }

        const result = await response.json()
        return { labels: result.data || [] }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

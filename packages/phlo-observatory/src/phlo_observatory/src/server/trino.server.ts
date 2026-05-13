/**
 * Trino Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { apiGet, apiPost } from '@/server/phlo-api'
import { camelizeKeys } from '@/utils/caseTransform'

// Types for Trino responses
interface TrinoConnectionStatus {
  connected: boolean
  error?: string
  clusterVersion?: string
}

export interface DataRow {
  [key: string]: string | number | boolean | null | undefined
}

export interface DataPreviewResult {
  columns: Array<string>
  columnTypes: Array<string>
  rows: Array<DataRow>
  totalRows?: number
  hasMore: boolean
}

interface ColumnProfile {
  column: string
  type: string
  nullCount: number
  nullPercentage: number
  distinctCount: number
  minValue?: string
  maxValue?: string
  sampleValues?: Array<string>
}

interface TableMetrics {
  rowCount: number
  sizeBytes?: number
  lastModified?: string
  partitionCount?: number
}

export interface QueryExecutionError {
  ok: false
  error: string
  kind: 'timeout' | 'trino' | 'validation'
}

export type QueryExecutionResult = DataPreviewResult & {
  effectiveQuery: string
}

// Python API response types (snake_case)
interface ApiConnectionStatus {
  connected: boolean
  error?: string
  cluster_version?: string
}

interface ApiDataPreviewResult {
  columns: Array<string>
  column_types: Array<string>
  rows: Array<DataRow>
  total_rows?: number
  has_more: boolean
}

interface ApiColumnProfile {
  column: string
  type: string
  null_count: number
  null_percentage: number
  distinct_count: number
  min_value?: string
  max_value?: string
}

interface ApiTableMetrics {
  row_count: number
  size_bytes?: number
}

interface ApiQueryResult extends ApiDataPreviewResult {
  effective_query?: string
}

// Transform functions
function transformPreviewResult(r: ApiDataPreviewResult): DataPreviewResult {
  return camelizeKeys<DataPreviewResult>(r)
}

/**
 * Check if Trino is reachable
 */
const checkTrinoConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { trinoUrl?: string } = {}) => input)
  .handler(async (): Promise<TrinoConnectionStatus> => {
    try {
      const result = await apiGet<ApiConnectionStatus>('/api/trino/connection')
      return camelizeKeys<TrinoConnectionStatus>(result)
    } catch (error) {
      return {
        connected: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Preview data from a table with pagination
 */
export const previewData = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      table: string
      branch?: string
      catalog?: string
      schema?: string
      limit?: number
      offset?: number
      trinoUrl?: string
      timeoutMs?: number
      maxLimit?: number
    }) => input,
  )
  .handler(
    async ({
      data: {
        table,
        branch = 'main',
        catalog,
        schema,
        limit = 100,
        offset = 0,
      },
    }): Promise<DataPreviewResult | { error: string }> => {
      try {
        const result = await apiGet<ApiDataPreviewResult | { error: string }>(
          `/api/trino/preview/${encodeURIComponent(table)}`,
          { branch, catalog, schema, limit, offset },
        )

        if ('error' in result) return result
        return transformPreviewResult(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get column statistics/profile
 */
const profileColumn = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      table: string
      column: string
      branch?: string
      catalog?: string
      schema?: string
      trinoUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(
    async ({
      data: { table, column, branch = 'main', catalog, schema },
    }): Promise<ColumnProfile | { error: string }> => {
      try {
        const result = await apiGet<ApiColumnProfile | { error: string }>(
          `/api/trino/profile/${encodeURIComponent(table)}/${encodeURIComponent(column)}`,
          { branch, catalog, schema },
        )

        if ('error' in result) return result
        return camelizeKeys<ColumnProfile>(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get table-level metrics
 */
const getTableMetrics = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      table: string
      branch?: string
      catalog?: string
      schema?: string
      trinoUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(
    async ({
      data: { table, branch = 'main', catalog, schema },
    }): Promise<TableMetrics | { error: string }> => {
      try {
        const result = await apiGet<ApiTableMetrics | { error: string }>(
          `/api/trino/metrics/${encodeURIComponent(table)}`,
          { branch, catalog, schema },
        )

        if ('error' in result) return result
        return camelizeKeys<TableMetrics>(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Run an arbitrary read-only query
 */
export const executeQuery = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      query: string
      branch?: string
      catalog?: string
      schema?: string
      trinoUrl?: string
      timeoutMs?: number
      readOnlyMode?: boolean
      defaultLimit?: number
      maxLimit?: number
      allowUnsafe?: boolean
    }) => input,
  )
  .handler(
    async ({
      data: {
        query,
        branch = 'main',
        catalog,
        schema,
        readOnlyMode = true,
        defaultLimit = 100,
        maxLimit = 5000,
      },
    }): Promise<QueryExecutionResult | QueryExecutionError> => {
      try {
        const result = await apiPost<ApiQueryResult | QueryExecutionError>(
          '/api/trino/query',
          {
            query,
            branch,
            catalog,
            schema,
            read_only_mode: readOnlyMode,
            default_limit: defaultLimit,
            max_limit: maxLimit,
          },
        )

        if ('ok' in result && result.ok === false) return result
        if ('error' in result) {
          return { ok: false, error: result.error, kind: 'trino' }
        }

        return {
          ...transformPreviewResult(result),
          effectiveQuery: result.effective_query ?? query,
        }
      } catch (error) {
        return {
          ok: false,
          error: error instanceof Error ? error.message : 'Unknown error',
          kind: 'trino',
        }
      }
    },
  )

/**
 * Query a table with specific column value filters
 */
const queryTableWithFilters = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      tableName: string
      schema: string
      filters: Record<string, unknown>
      catalog?: string
      trinoUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(
    async ({
      data: { tableName, schema, filters, catalog },
    }): Promise<DataPreviewResult | { error: string }> => {
      try {
        const result = await apiPost<ApiDataPreviewResult | { error: string }>(
          '/api/trino/query-with-filters',
          {
            table_name: tableName,
            schema,
            catalog: catalog || 'iceberg',
            filters,
            limit: 10,
          },
        )

        if ('error' in result) return { error: result.error }
        return transformPreviewResult(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get a single row by its _phlo_row_id
 */
export const getRowById = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      table: string
      rowId: string
      catalog?: string
      schema?: string
      trinoUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(
    async ({
      data: { table, rowId, catalog, schema },
    }): Promise<DataPreviewResult | { error: string }> => {
      try {
        const result = await apiGet<ApiDataPreviewResult | { error: string }>(
          `/api/trino/row/${encodeURIComponent(table)}/${encodeURIComponent(rowId)}`,
          { catalog, schema },
        )

        if ('error' in result) return result
        return transformPreviewResult(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

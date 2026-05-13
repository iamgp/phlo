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

export interface QueryExecutionError {
  ok: false
  error: string
  kind: 'timeout' | 'trino' | 'validation'
}

export type QueryExecutionResult = DataPreviewResult & {
  effectiveQuery: string
}

// Python API response types (snake_case)
interface ApiDataPreviewResult {
  columns: Array<string>
  column_types: Array<string>
  rows: Array<DataRow>
  total_rows?: number
  has_more: boolean
}

interface ApiQueryResult extends ApiDataPreviewResult {
  effective_query?: string
}

// Transform functions
function transformPreviewResult(r: ApiDataPreviewResult): DataPreviewResult {
  return camelizeKeys<DataPreviewResult>(r)
}

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

/**
 * Trino Server Functions
 *
 * Server-side functions for executing queries against Trino via HTTP API.
 * Enables data preview, column profiling, and table metrics in Observatory.
 */

import { createServerFn } from '@tanstack/react-start'

import type {
  QueryExecutionError,
  QueryGuardrails,
} from '@/server/queryGuardrails'
import { validateAndRewriteQuery } from '@/server/queryGuardrails'
import {
  isProbablyQualifiedTable,
  qualifyTableName,
} from '@/utils/sqlIdentifiers'

// Types for Trino responses
export interface TrinoConnectionStatus {
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

export interface ColumnProfile {
  column: string
  type: string
  nullCount: number
  nullPercentage: number
  distinctCount: number
  minValue?: string
  maxValue?: string
  sampleValues?: Array<string>
}

export interface TableMetrics {
  rowCount: number
  sizeBytes?: number
  lastModified?: string
  partitionCount?: number
}

const DEFAULT_CATALOG = 'iceberg'
const DEFAULT_TRINO_URL = 'http://localhost:8080'

function resolveTrinoUrl(override?: string): string {
  if (override && override.trim()) return override
  return process.env.TRINO_URL || DEFAULT_TRINO_URL
}

export type { QueryExecutionError } from '@/server/queryGuardrails'

export type QueryExecutionResult = DataPreviewResult & {
  effectiveQuery: string
}

/**
 * Execute a query against Trino and wait for results
 * Trino uses a multi-stage query execution model
 */
async function executeTrinoQuery(
  query: string,
  catalog: string = DEFAULT_CATALOG,
  schema: string = 'main',
  options?: { trinoUrl?: string; timeoutMs?: number },
): Promise<
  | { columns: Array<string>; columnTypes: Array<string>; rows: Array<DataRow> }
  | QueryExecutionError
> {
  const trinoUrl = resolveTrinoUrl(options?.trinoUrl)
  const timeoutMs = options?.timeoutMs ?? 30_000

  try {
    // Submit query
    const submitResponse = await fetch(`${trinoUrl}/v1/statement`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
        'X-Trino-User': 'observatory',
        'X-Trino-Catalog': catalog,
        'X-Trino-Schema': schema,
      },
      body: query,
      signal: AbortSignal.timeout(timeoutMs),
    })

    if (!submitResponse.ok) {
      const errorText = await submitResponse.text()
      return { ok: false, error: `Trino error: ${errorText}`, kind: 'trino' }
    }

    let result = await submitResponse.json()

    // Poll until query completes
    const maxPolls = 100
    let polls = 0
    const allData: Array<Array<unknown>> = []
    let columns: Array<string> = []
    let columnTypes: Array<string> = []

    while (result.nextUri && polls < maxPolls) {
      polls++
      await new Promise((resolve) => setTimeout(resolve, 100)) // Small delay

      const pollResponse = await fetch(result.nextUri, {
        headers: {
          'X-Trino-User': 'observatory',
        },
        signal: AbortSignal.timeout(timeoutMs),
      })

      if (!pollResponse.ok) {
        const errorText = await pollResponse.text()
        return {
          ok: false,
          error: `Trino poll error: ${errorText}`,
          kind: 'trino',
        }
      }

      result = await pollResponse.json()

      // Extract columns on first response with them
      if (result.columns && columns.length === 0) {
        columns = result.columns.map((c: { name: string }) => c.name)
        columnTypes = result.columns.map((c: { type: string }) => c.type)
      }

      // Collect data
      if (result.data) {
        allData.push(...result.data)
      }

      // Check for errors
      if (result.error) {
        return {
          ok: false,
          error: result.error.message || 'Query failed',
          kind: 'trino',
        }
      }
    }

    // Convert array rows to objects
    const rows: Array<DataRow> = allData.map((row) => {
      const obj: DataRow = {}
      columns.forEach((col, idx) => {
        obj[col] = (row as Array<string | number | boolean | null>)[idx]
      })
      return obj
    })

    return { columns, columnTypes, rows }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    if (message.toLowerCase().includes('timeout')) {
      return { ok: false, error: message, kind: 'timeout' }
    }
    return { ok: false, error: message, kind: 'trino' }
  }
}

/**
 * Check if Trino is reachable
 */
export const checkTrinoConnection = createServerFn()
  .inputValidator((input: { trinoUrl?: string } = {}) => input)
  .handler(async ({ data }): Promise<TrinoConnectionStatus> => {
    const trinoUrl = resolveTrinoUrl(data.trinoUrl)

    try {
      const response = await fetch(`${trinoUrl}/v1/info`, {
        signal: AbortSignal.timeout(5000),
      })

      if (!response.ok) {
        return {
          connected: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      const info = await response.json()

      return {
        connected: true,
        clusterVersion: info.nodeVersion?.version || 'unknown',
      }
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
        trinoUrl,
        timeoutMs,
        maxLimit,
      },
    }): Promise<DataPreviewResult | { error: string }> => {
      const effectiveLimit = Math.min(limit, maxLimit ?? limit)
      // Build query - note: Trino doesn't support standard OFFSET syntax
      // For pagination, use FETCH FIRST / OFFSET FETCH syntax if needed
      // For simple preview, just use LIMIT
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const effectiveSchema = schema ?? branch // In Nessie, the branch is the schema
      const resolvedTable = isProbablyQualifiedTable(table)
        ? table
        : qualifyTableName({
            catalog: effectiveCatalog,
            schema: effectiveSchema,
            table,
          })

      // Trino uses "OFFSET n ROWS FETCH FIRST m ROWS ONLY" syntax but for simplicity just use LIMIT
      const query =
        offset > 0
          ? `SELECT * FROM ${resolvedTable} OFFSET ${offset} ROWS FETCH FIRST ${effectiveLimit} ROWS ONLY`
          : `SELECT * FROM ${resolvedTable} LIMIT ${effectiveLimit}`

      const result = await executeTrinoQuery(
        query,
        effectiveCatalog,
        effectiveSchema,
        {
          trinoUrl,
          timeoutMs,
        },
      )

      if ('error' in result) {
        return { error: result.error }
      }

      return {
        columns: result.columns,
        columnTypes: result.columnTypes,
        rows: result.rows,
        hasMore: result.rows.length === effectiveLimit,
      }
    },
  )

/**
 * Get column statistics/profile
 */
export const profileColumn = createServerFn()
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
      data: {
        table,
        column,
        branch = 'main',
        catalog,
        schema,
        trinoUrl,
        timeoutMs,
      },
    }): Promise<ColumnProfile | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const effectiveSchema = schema ?? branch
      const resolvedTable = isProbablyQualifiedTable(table)
        ? table
        : qualifyTableName({
            catalog: effectiveCatalog,
            schema: effectiveSchema,
            table,
          })

      // Build profiling query
      const query = `
        SELECT
          COUNT(*) as total_count,
          COUNT("${column}") as non_null_count,
          COUNT(DISTINCT "${column}") as distinct_count,
          MIN(CAST("${column}" AS VARCHAR)) as min_value,
          MAX(CAST("${column}" AS VARCHAR)) as max_value
        FROM ${resolvedTable}
      `

      const result = await executeTrinoQuery(
        query,
        effectiveCatalog,
        effectiveSchema,
        {
          trinoUrl,
          timeoutMs,
        },
      )

      if ('error' in result) {
        return { error: result.error }
      }

      if (result.rows.length === 0) {
        return { error: 'No data returned from profile query' }
      }

      const row = result.rows[0]
      const totalCount = Number(row.total_count) || 0
      const nonNullCount = Number(row.non_null_count) || 0
      const nullCount = totalCount - nonNullCount

      return {
        column,
        type: 'unknown', // Would need schema lookup
        nullCount,
        nullPercentage: totalCount > 0 ? (nullCount / totalCount) * 100 : 0,
        distinctCount: Number(row.distinct_count) || 0,
        minValue: row.min_value as string | undefined,
        maxValue: row.max_value as string | undefined,
      }
    },
  )

/**
 * Get table-level metrics
 */
export const getTableMetrics = createServerFn()
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
      data: { table, branch = 'main', catalog, schema, trinoUrl, timeoutMs },
    }): Promise<TableMetrics | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const effectiveSchema = schema ?? branch
      const resolvedTable = isProbablyQualifiedTable(table)
        ? table
        : qualifyTableName({
            catalog: effectiveCatalog,
            schema: effectiveSchema,
            table,
          })

      const query = `SELECT COUNT(*) as row_count FROM ${resolvedTable}`

      const result = await executeTrinoQuery(
        query,
        effectiveCatalog,
        effectiveSchema,
        {
          trinoUrl,
          timeoutMs,
        },
      )

      if ('error' in result) {
        return { error: result.error }
      }

      if (result.rows.length === 0) {
        return { error: 'No data returned from count query' }
      }

      return {
        rowCount: Number(result.rows[0].row_count) || 0,
      }
    },
  )

/**
 * Run an arbitrary read-only query (for advanced users)
 */
export const executeQuery = createServerFn()
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
        trinoUrl,
        timeoutMs,
        readOnlyMode = true,
        defaultLimit = 100,
        maxLimit = 5000,
        allowUnsafe = false,
      },
    }): Promise<QueryExecutionResult | QueryExecutionError> => {
      const guardrails: QueryGuardrails = {
        readOnlyMode,
        defaultLimit,
        maxLimit,
      }

      const validated = validateAndRewriteQuery({
        query,
        guardrails,
        allowUnsafe,
      })

      if (!validated.ok) {
        return validated
      }

      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const effectiveSchema = schema ?? branch

      const result = await executeTrinoQuery(
        validated.effectiveQuery,
        effectiveCatalog,
        effectiveSchema,
        {
          trinoUrl,
          timeoutMs,
        },
      )

      if ('error' in result) {
        return result
      }

      return {
        columns: result.columns,
        columnTypes: result.columnTypes,
        rows: result.rows,
        hasMore: false,
        effectiveQuery: validated.effectiveQuery,
      }
    },
  )

/**
 * Query a table with specific column value filters
 * Used for tracking row data across transformations
 */
export const queryTableWithFilters = createServerFn()
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
      data: { tableName, schema, filters, catalog, trinoUrl, timeoutMs },
    }): Promise<DataPreviewResult | { error: string }> => {
      // Build WHERE clause from filters
      const whereConditions = Object.entries(filters)
        .map(([column, value]) => {
          if (value === null || value === undefined) {
            return `${column} IS NULL`
          }
          if (typeof value === 'string') {
            // Escape single quotes in string values
            const escapedValue = value.replace(/'/g, "''")
            return `${column} = '${escapedValue}'`
          }
          if (typeof value === 'number') {
            return `${column} = ${value}`
          }
          if (typeof value === 'boolean') {
            return `${column} = ${value}`
          }
          return null
        })
        .filter(Boolean)
        .join(' AND ')

      if (whereConditions.length === 0) {
        return {
          columns: [],
          columnTypes: [],
          rows: [],
          hasMore: false,
        }
      }

      const resolvedTable = qualifyTableName({
        catalog: catalog ?? DEFAULT_CATALOG,
        schema,
        table: tableName,
      })
      const query = `SELECT * FROM ${resolvedTable} WHERE ${whereConditions} LIMIT 10`

      const result = await executeTrinoQuery(
        query,
        catalog ?? DEFAULT_CATALOG,
        schema,
        {
          trinoUrl,
          timeoutMs,
        },
      )

      if ('error' in result) {
        return { error: result.error }
      }

      return {
        columns: result.columns,
        columnTypes: result.columnTypes,
        rows: result.rows,
        hasMore: false,
      }
    },
  )

/**
 * Get a single row by its _phlo_row_id
 * Used for deep linking to row-level data journeys
 */
export const getRowById = createServerFn()
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
      data: { table, rowId, catalog, schema, trinoUrl, timeoutMs },
    }): Promise<DataPreviewResult | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const effectiveSchema = schema ?? 'main'
      const resolvedTable = isProbablyQualifiedTable(table)
        ? table
        : qualifyTableName({
            catalog: effectiveCatalog,
            schema: effectiveSchema,
            table,
          })

      // Escape single quotes in rowId to prevent SQL injection
      const escapedRowId = rowId.replace(/'/g, "''")
      const query = `SELECT * FROM ${resolvedTable} WHERE "_phlo_row_id" = '${escapedRowId}' LIMIT 1`

      const result = await executeTrinoQuery(
        query,
        effectiveCatalog,
        effectiveSchema,
        {
          trinoUrl,
          timeoutMs,
        },
      )

      if ('error' in result) {
        return { error: result.error }
      }

      if (result.rows.length === 0) {
        return { error: 'Row not found' }
      }

      return {
        columns: result.columns,
        columnTypes: result.columnTypes,
        rows: result.rows,
        hasMore: false,
      }
    },
  )

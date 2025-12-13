/**
 * Trino Server Functions
 *
 * Server-side functions for executing queries against Trino via HTTP API.
 * Enables data preview, column profiling, and table metrics in Observatory.
 */

import { createServerFn } from '@tanstack/react-start'

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

// Get Trino URL from environment
const getTrinoUrl = () => process.env.TRINO_URL || 'http://localhost:8080'

/**
 * Execute a query against Trino and wait for results
 * Trino uses a multi-stage query execution model
 */
async function executeTrinoQuery(
  query: string,
  catalog: string = 'iceberg',
  schema: string = 'main',
): Promise<
  | { columns: Array<string>; columnTypes: Array<string>; rows: Array<DataRow> }
  | { error: string }
> {
  const trinoUrl = getTrinoUrl()

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
      signal: AbortSignal.timeout(30000),
    })

    if (!submitResponse.ok) {
      const errorText = await submitResponse.text()
      return { error: `Trino error: ${errorText}` }
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
        signal: AbortSignal.timeout(30000),
      })

      if (!pollResponse.ok) {
        const errorText = await pollResponse.text()
        return { error: `Trino poll error: ${errorText}` }
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
        return { error: result.error.message || 'Query failed' }
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
    return { error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

/**
 * Check if Trino is reachable
 */
export const checkTrinoConnection = createServerFn().handler(
  async (): Promise<TrinoConnectionStatus> => {
    const trinoUrl = getTrinoUrl()

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
  },
)

/**
 * Preview data from a table with pagination
 */
export const previewData = createServerFn()
  .inputValidator(
    (input: {
      table: string
      branch?: string
      limit?: number
      offset?: number
    }) => input,
  )
  .handler(
    async ({
      data: { table, branch = 'main', limit = 100, offset = 0 },
    }): Promise<DataPreviewResult | { error: string }> => {
      // Build query - note: Trino doesn't support standard OFFSET syntax
      // For pagination, use FETCH FIRST / OFFSET FETCH syntax if needed
      // For simple preview, just use LIMIT
      const catalog = 'iceberg'
      const schema = branch // In Nessie, the branch is the schema

      // Trino uses "OFFSET n ROWS FETCH FIRST m ROWS ONLY" syntax but for simplicity just use LIMIT
      const query =
        offset > 0
          ? `SELECT * FROM ${table} OFFSET ${offset} ROWS FETCH FIRST ${limit} ROWS ONLY`
          : `SELECT * FROM ${table} LIMIT ${limit}`

      const result = await executeTrinoQuery(query, catalog, schema)

      if ('error' in result) {
        return result
      }

      return {
        columns: result.columns,
        columnTypes: result.columnTypes,
        rows: result.rows,
        hasMore: result.rows.length === limit,
      }
    },
  )

/**
 * Get column statistics/profile
 */
export const profileColumn = createServerFn()
  .inputValidator(
    (input: { table: string; column: string; branch?: string }) => input,
  )
  .handler(
    async ({
      data: { table, column, branch = 'main' },
    }): Promise<ColumnProfile | { error: string }> => {
      const catalog = 'iceberg'
      const schema = branch

      // Build profiling query
      const query = `
        SELECT
          COUNT(*) as total_count,
          COUNT("${column}") as non_null_count,
          COUNT(DISTINCT "${column}") as distinct_count,
          MIN(CAST("${column}" AS VARCHAR)) as min_value,
          MAX(CAST("${column}" AS VARCHAR)) as max_value
        FROM ${table}
      `

      const result = await executeTrinoQuery(query, catalog, schema)

      if ('error' in result) {
        return result
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
  .inputValidator((input: { table: string; branch?: string }) => input)
  .handler(
    async ({
      data: { table, branch = 'main' },
    }): Promise<TableMetrics | { error: string }> => {
      const catalog = 'iceberg'
      const schema = branch

      const query = `SELECT COUNT(*) as row_count FROM ${table}`

      const result = await executeTrinoQuery(query, catalog, schema)

      if ('error' in result) {
        return result
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
  .inputValidator((input: { query: string; branch?: string }) => input)
  .handler(
    async ({
      data: { query, branch = 'main' },
    }): Promise<DataPreviewResult | { error: string }> => {
      // Safety check - only allow SELECT queries
      const trimmedQuery = query.trim().toUpperCase()
      if (
        !trimmedQuery.startsWith('SELECT') &&
        !trimmedQuery.startsWith('SHOW') &&
        !trimmedQuery.startsWith('DESCRIBE')
      ) {
        return { error: 'Only SELECT, SHOW, and DESCRIBE queries are allowed' }
      }

      const catalog = 'iceberg'
      const schema = branch

      const result = await executeTrinoQuery(query, catalog, schema)

      if ('error' in result) {
        return result
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
 * Query a table with specific column value filters
 * Used for tracking row data across transformations
 */
export const queryTableWithFilters = createServerFn()
  .inputValidator(
    (input: {
      tableName: string
      schema: string
      filters: Record<string, unknown>
    }) => input,
  )
  .handler(
    async ({
      data: { tableName, schema, filters },
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

      const query = `SELECT * FROM iceberg.${schema}.${tableName} WHERE ${whereConditions} LIMIT 10`

      const result = await executeTrinoQuery(query, 'iceberg', schema)

      if ('error' in result) {
        return result
      }

      return {
        columns: result.columns,
        columnTypes: result.columnTypes,
        rows: result.rows,
        hasMore: false,
      }
    },
  )

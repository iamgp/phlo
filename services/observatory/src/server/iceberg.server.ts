/**
 * Iceberg Catalog Server Functions
 *
 * Server-side functions for querying Iceberg tables via Trino.
 * Provides table listing, schema info, and snapshot history.
 */

import { createServerFn } from '@tanstack/react-start'

// Types for table metadata
export interface IcebergTable {
  catalog: string
  schema: string
  name: string
  fullName: string
  layer: 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'
}

export interface TableColumn {
  name: string
  type: string
  nullable: boolean
  comment?: string
}

export interface TableMetadata {
  table: IcebergTable
  columns: Array<TableColumn>
  rowCount?: number
  lastModified?: string
}

// Get Trino URL from environment
const getTrinoUrl = () => process.env.TRINO_URL || 'http://localhost:8080'

/**
 * Query Trino and return results
 */
async function queryTrino<T>(
  sql: string,
): Promise<{ data: Array<T>; columns: Array<string> } | { error: string }> {
  const trinoUrl = getTrinoUrl()

  try {
    // Submit query
    const submitResponse = await fetch(`${trinoUrl}/v1/statement`, {
      method: 'POST',
      headers: {
        'X-Trino-User': 'observatory',
        'X-Trino-Catalog': 'iceberg',
        // Not setting X-Trino-Schema since we use fully-qualified table names
      },
      body: sql,
      signal: AbortSignal.timeout(30000),
    })

    if (!submitResponse.ok) {
      return {
        error: `HTTP ${submitResponse.status}: ${submitResponse.statusText}`,
      }
    }

    let result = await submitResponse.json()

    // Accumulate data across all polling responses
    // Trino returns data incrementally, so we need to collect all of it
    const allData: Array<Array<unknown>> = []
    if (result.data) {
      allData.push(...result.data)
    }

    // Poll for results until no more nextUri
    while (result.nextUri) {
      await new Promise((resolve) => setTimeout(resolve, 100))
      const pollResponse = await fetch(result.nextUri, {
        signal: AbortSignal.timeout(30000),
      })
      result = await pollResponse.json()

      // Accumulate data from this response
      if (result.data) {
        allData.push(...result.data)
      }
    }

    // Replace result.data with accumulated data
    result.data = allData

    console.log(
      '[queryTrino] Final result:',
      JSON.stringify(result, null, 2).substring(0, 500),
    )

    if (result.error) {
      return { error: result.error.message || 'Query failed' }
    }

    const columns = (result.columns || []).map((c: { name: string }) => c.name)
    const data = (result.data || []).map((row: Array<unknown>) => {
      const obj: Record<string, unknown> = {}
      columns.forEach((col: string, idx: number) => {
        obj[col] = row[idx]
      })
      return obj as T
    })

    console.log(
      '[queryTrino] Parsed columns:',
      columns,
      'data count:',
      data.length,
    )

    return { data, columns }
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Query failed' }
  }
}

/**
 * Infer data layer from table name prefix
 * This is the primary method since Iceberg schemas may not match medallion layers
 */
function inferLayer(name: string): IcebergTable['layer'] {
  const lower = name.toLowerCase()
  // Bronze: raw ingestion tables from DLT
  if (lower.startsWith('dlt_')) return 'bronze'
  // Silver: staged/cleaned tables
  if (lower.startsWith('stg_')) return 'silver'
  // Gold: curated fact/dimension tables
  if (lower.startsWith('fct_') || lower.startsWith('dim_')) return 'gold'
  // Publish: mart tables for BI consumption
  if (lower.startsWith('mrt_') || lower.startsWith('publish_')) return 'publish'
  // Fallback checks for less common patterns
  if (lower.includes('raw')) return 'bronze'
  if (lower.includes('staging')) return 'silver'
  return 'unknown'
}

/**
 * Get all tables from Iceberg catalog
 */
export const getTables = createServerFn()
  .inputValidator((input: { branch?: string }) => input)
  .handler(
    async ({
      data: { branch = 'main' },
    }): Promise<Array<IcebergTable> | { error: string }> => {
      // Query for schemas first, then tables in each schema
      // The Iceberg catalog uses schema names like 'bronze', 'raw', 'silver', 'gold', 'publish'
      const schemasToQuery = ['bronze', 'silver', 'gold', 'raw', 'publish']
      const allTables: Array<IcebergTable> = []
      const errors: Array<string> = []

      console.log('[getTables] Starting to query schemas:', schemasToQuery)

      for (const schema of schemasToQuery) {
        const sql = `SHOW TABLES FROM iceberg.${schema}`
        console.log('[getTables] Querying:', sql)
        const result = await queryTrino<{ Table: string }>(sql)

        // Skip schemas that don't exist or have errors
        if ('error' in result) {
          console.log('[getTables] Error for schema', schema, ':', result.error)
          errors.push(`${schema}: ${result.error}`)
          continue
        }

        console.log(
          '[getTables] Found',
          result.data.length,
          'tables in',
          schema,
        )
        for (const row of result.data) {
          allTables.push({
            catalog: 'iceberg',
            schema: schema,
            name: row.Table,
            fullName: `iceberg.${schema}.${row.Table}`,
            layer: inferLayerFromSchema(schema, row.Table),
          })
        }
      }

      console.log('[getTables] Total tables found:', allTables.length)

      if (allTables.length === 0 && errors.length > 0) {
        // Return a combined error message if all schemas failed
        return { error: errors.join('; ') }
      }

      if (allTables.length === 0) {
        // Fall back to trying the branch as a schema name (for Nessie-based setups)
        const sql = `SHOW TABLES FROM iceberg."${branch}"`
        console.log('[getTables] Fallback query:', sql)
        const result = await queryTrino<{ Table: string }>(sql)

        if ('error' in result) {
          return result
        }

        for (const row of result.data) {
          allTables.push({
            catalog: 'iceberg',
            schema: branch,
            name: row.Table,
            fullName: `iceberg."${branch}".${row.Table}`,
            layer: inferLayer(row.Table),
          })
        }
      }

      // Sort by layer then name
      const layerOrder = {
        bronze: 0,
        silver: 1,
        gold: 2,
        publish: 3,
        unknown: 4,
      }
      allTables.sort(
        (a, b) =>
          layerOrder[a.layer] - layerOrder[b.layer] ||
          a.name.localeCompare(b.name),
      )

      return allTables
    },
  )

/**
 * Infer layer - TABLE NAME takes precedence over schema name
 * This is because Iceberg schemas may not match the medallion architecture
 */
function inferLayerFromSchema(
  schema: string,
  tableName: string,
): IcebergTable['layer'] {
  // First, try to infer from table name (most reliable)
  const fromTableName = inferLayer(tableName)
  if (fromTableName !== 'unknown') {
    return fromTableName
  }

  // Fall back to schema name for tables without standard prefixes
  const s = schema.toLowerCase()
  if (s === 'bronze' || s === 'raw') return 'bronze'
  if (s === 'silver' || s === 'staging') return 'silver'
  if (s === 'gold' || s === 'curated') return 'gold'
  if (s === 'publish' || s === 'marts') return 'publish'

  return 'unknown'
}

/**
 * Get schema for a specific table
 */
export const getTableSchema = createServerFn()
  .inputValidator((input: { table: string; branch?: string }) => input)
  .handler(
    async ({
      data: { table, branch = 'main' },
    }): Promise<Array<TableColumn> | { error: string }> => {
      const sql = `DESCRIBE iceberg."${branch}"."${table}"`
      const result = await queryTrino<{
        Column: string
        Type: string
        Extra: string
        Comment: string
      }>(sql)

      if ('error' in result) {
        return result
      }

      return result.data.map((row) => ({
        name: row.Column,
        type: row.Type,
        nullable: !row.Extra?.includes('NOT NULL'),
        comment: row.Comment || undefined,
      }))
    },
  )

/**
 * Get row count for a table
 */
export const getTableRowCount = createServerFn()
  .inputValidator((input: { table: string; branch?: string }) => input)
  .handler(
    async ({
      data: { table, branch = 'main' },
    }): Promise<number | { error: string }> => {
      const sql = `SELECT COUNT(*) as cnt FROM iceberg."${branch}"."${table}"`
      const result = await queryTrino<{ cnt: number }>(sql)

      if ('error' in result) {
        return result
      }

      return result.data[0]?.cnt ?? 0
    },
  )

/**
 * Get table metadata including schema and stats
 */
export const getTableMetadata = createServerFn()
  .inputValidator((input: { table: string; branch?: string }) => input)
  .handler(
    async ({
      data: { table, branch = 'main' },
    }): Promise<TableMetadata | { error: string }> => {
      // Get schema
      const schemaResult = await getTableSchema({ data: { table, branch } })
      if ('error' in schemaResult) {
        return schemaResult
      }

      // Get row count (optional - don't fail if this errors)
      let rowCount: number | undefined
      try {
        const countResult = await getTableRowCount({ data: { table, branch } })
        if (typeof countResult === 'number') {
          rowCount = countResult
        }
      } catch {
        // Row count is optional
      }

      return {
        table: {
          catalog: 'iceberg',
          schema: branch,
          name: table,
          fullName: `iceberg."${branch}"."${table}"`,
          layer: inferLayer(table),
        },
        columns: schemaResult,
        rowCount,
      }
    },
  )

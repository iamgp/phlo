/**
 * Iceberg Catalog Server Functions
 *
 * Server-side functions for querying Iceberg tables via Trino.
 * Provides table listing, schema info, and snapshot history.
 */

import { createServerFn } from '@tanstack/react-start'

import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { quoteIdentifier } from '@/utils/sqlIdentifiers'

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

const DEFAULT_CATALOG = 'iceberg'
const DEFAULT_TRINO_URL = 'http://localhost:8080'

function resolveTrinoUrl(override?: string): string {
  if (override && override.trim()) return override
  return process.env.TRINO_URL || DEFAULT_TRINO_URL
}

/**
 * Query Trino and return results
 */
async function queryTrino<T>(
  sql: string,
  options?: { trinoUrl?: string; timeoutMs?: number; catalog?: string },
): Promise<{ data: Array<T>; columns: Array<string> } | { error: string }> {
  const trinoUrl = resolveTrinoUrl(options?.trinoUrl)
  const timeoutMs = options?.timeoutMs ?? 30_000
  const catalog = options?.catalog ?? DEFAULT_CATALOG

  try {
    // Submit query
    const submitResponse = await fetch(`${trinoUrl}/v1/statement`, {
      method: 'POST',
      headers: {
        'X-Trino-User': 'observatory',
        'X-Trino-Catalog': catalog,
        // Not setting X-Trino-Schema since we use fully-qualified table names
      },
      body: sql,
      signal: AbortSignal.timeout(timeoutMs),
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
        headers: {
          'X-Trino-User': 'observatory',
        },
        signal: AbortSignal.timeout(timeoutMs),
      })
      result = await pollResponse.json()

      // Accumulate data from this response
      if (result.data) {
        allData.push(...result.data)
      }
    }

    // Replace result.data with accumulated data
    result.data = allData

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
async function fetchTables(
  branch: string,
  catalog: string,
  preferredSchema: string | undefined,
  trinoUrl: string | undefined,
  timeoutMs: number | undefined,
): Promise<Array<IcebergTable> | { error: string }> {
  const schemasToQuery = ['bronze', 'silver', 'gold', 'raw', 'marts', 'publish']
  if (preferredSchema && schemasToQuery.includes(preferredSchema)) {
    schemasToQuery.sort((a, b) =>
      a === preferredSchema ? -1 : b === preferredSchema ? 1 : 0,
    )
  }
  const allTables: Array<IcebergTable> = []
  const seenTables = new Set<string>()
  const errors: Array<string> = []

  for (const schema of schemasToQuery) {
    const sql = `SHOW TABLES FROM ${quoteIdentifier(catalog)}.${quoteIdentifier(schema)}`
    const result = await queryTrino<{ Table: string }>(sql, {
      trinoUrl,
      timeoutMs,
      catalog,
    })

    if ('error' in result) {
      errors.push(`${schema}: ${result.error}`)
      continue
    }

    for (const row of result.data) {
      if (!seenTables.has(row.Table)) {
        seenTables.add(row.Table)
        allTables.push({
          catalog,
          schema: schema,
          name: row.Table,
          fullName: `${quoteIdentifier(catalog)}.${quoteIdentifier(schema)}.${quoteIdentifier(row.Table)}`,
          layer: inferLayerFromSchema(schema, row.Table),
        })
      }
    }
  }

  if (allTables.length === 0 && errors.length > 0) {
    return { error: errors.join('; ') }
  }

  if (allTables.length === 0) {
    const sql = `SHOW TABLES FROM ${quoteIdentifier(catalog)}.${quoteIdentifier(branch)}`
    const result = await queryTrino<{ Table: string }>(sql, {
      trinoUrl,
      timeoutMs,
      catalog,
    })

    if ('error' in result) {
      return result
    }

    for (const row of result.data) {
      allTables.push({
        catalog,
        schema: branch,
        name: row.Table,
        fullName: `${quoteIdentifier(catalog)}.${quoteIdentifier(branch)}.${quoteIdentifier(row.Table)}`,
        layer: inferLayer(row.Table),
      })
    }
  }

  const layerOrder = { bronze: 0, silver: 1, gold: 2, publish: 3, unknown: 4 }
  allTables.sort(
    (a, b) =>
      layerOrder[a.layer] - layerOrder[b.layer] || a.name.localeCompare(b.name),
  )

  return allTables
}

export const getTables = createServerFn()
  .inputValidator(
    (input: {
      branch?: string
      catalog?: string
      preferredSchema?: string
      trinoUrl?: string
      timeoutMs?: number
    }) => input,
  )
  .handler(
    async ({
      data: { branch = 'main', catalog, preferredSchema, trinoUrl, timeoutMs },
    }): Promise<Array<IcebergTable> | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const key = cacheKeys.tables(effectiveCatalog, branch)

      return withCache(
        () =>
          fetchTables(
            branch,
            effectiveCatalog,
            preferredSchema,
            trinoUrl,
            timeoutMs,
          ),
        key,
        cacheTTL.tables,
      )
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

async function fetchTableSchema(
  table: string,
  branch: string,
  catalog: string,
): Promise<Array<TableColumn> | { error: string }> {
  const sql = `DESCRIBE ${quoteIdentifier(catalog)}.${quoteIdentifier(branch)}.${quoteIdentifier(table)}`
  const result = await queryTrino<{
    Column: string
    Type: string
    Extra: string
    Comment: string
  }>(sql, { catalog })

  if ('error' in result) {
    return result
  }

  return result.data.map((row) => ({
    name: row.Column,
    type: row.Type,
    nullable: !row.Extra?.includes('NOT NULL'),
    comment: row.Comment || undefined,
  }))
}

export const getTableSchema = createServerFn()
  .inputValidator(
    (input: {
      table: string
      schema?: string
      branch?: string
      catalog?: string
    }) => input,
  )
  .handler(
    async ({
      data: { table, schema, branch = 'main', catalog },
    }): Promise<Array<TableColumn> | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const effectiveSchema = schema ?? branch
      const key = cacheKeys.tableSchema(
        effectiveCatalog,
        effectiveSchema,
        table,
      )

      return withCache(
        () => fetchTableSchema(table, effectiveSchema, effectiveCatalog),
        key,
        cacheTTL.tableSchema,
      )
    },
  )

/**
 * Get row count for a table
 */
export const getTableRowCount = createServerFn()
  .inputValidator(
    (input: { table: string; branch?: string; catalog?: string }) => input,
  )
  .handler(
    async ({
      data: { table, branch = 'main', catalog },
    }): Promise<number | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const sql = `SELECT COUNT(*) as cnt FROM ${quoteIdentifier(effectiveCatalog)}.${quoteIdentifier(branch)}.${quoteIdentifier(table)}`
      const result = await queryTrino<{ cnt: number }>(sql, {
        catalog: effectiveCatalog,
      })

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
  .inputValidator(
    (input: { table: string; branch?: string; catalog?: string }) => input,
  )
  .handler(
    async ({
      data: { table, branch = 'main', catalog },
    }): Promise<TableMetadata | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      // Get schema
      const schemaResult = await getTableSchema({
        data: { table, branch, catalog: effectiveCatalog },
      })
      if ('error' in schemaResult) {
        return schemaResult
      }

      // Get row count (optional - don't fail if this errors)
      let rowCount: number | undefined
      try {
        const countResult = await getTableRowCount({
          data: { table, branch, catalog: effectiveCatalog },
        })
        if (typeof countResult === 'number') {
          rowCount = countResult
        }
      } catch {
        // Row count is optional
      }

      return {
        table: {
          catalog: effectiveCatalog,
          schema: branch,
          name: table,
          fullName: `${quoteIdentifier(effectiveCatalog)}.${quoteIdentifier(branch)}.${quoteIdentifier(table)}`,
          layer: inferLayer(table),
        },
        columns: schemaResult,
        rowCount,
      }
    },
  )

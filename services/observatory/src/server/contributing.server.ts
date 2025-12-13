/**
 * Contributing Rows Query Builder
 *
 * Builds deterministic Trino queries to retrieve the upstream ("contributing") rows
 * for a selected row in an aggregate or transformed table.
 *
 * Strategy:
 * - If `_phlo_row_id` is present and exists upstream: use it (1:1 transforms).
 * - Otherwise: filter upstream by `_phlo_partition_date` plus grain dimensions
 *   using explicit per-model mappings and safe fallbacks.
 */

import { createServerFn } from '@tanstack/react-start'

type Primitive = string | number | boolean | null | undefined

interface ResolveTableResult {
  schema: string
  table: string
  fullName: string
  columnTypes: Record<string, string>
}

const getTrinoUrl = () => process.env.TRINO_URL || 'http://localhost:8080'

function escapeSqlString(value: string): string {
  return value.replaceAll("'", "''")
}

function toSqlEquality(
  columnName: string,
  columnType: string,
  value: Primitive,
): string | null {
  if (value === null || value === undefined) return null

  const normalizedType = columnType.toLowerCase()

  // Timestamps are annoying to literal-type reliably across precisions; compare by varchar.
  if (normalizedType.startsWith('timestamp') || normalizedType.startsWith('time')) {
    const raw = String(value)
    const normalized = raw.replace(
      /(\.\d{1,6})$/,
      (match) => match.padEnd(7, '0'),
    )
    const padded = normalized.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
      ? `${normalized}.000000`
      : normalized
    return `cast("${columnName}" as varchar) = '${escapeSqlString(padded)}'`
  }

  if (normalizedType.startsWith('varchar') || normalizedType === 'varbinary') {
    return `"${columnName}" = '${escapeSqlString(String(value))}'`
  }

  if (
    normalizedType.startsWith('bigint') ||
    normalizedType.startsWith('integer') ||
    normalizedType.startsWith('smallint') ||
    normalizedType.startsWith('tinyint') ||
    normalizedType.startsWith('double') ||
    normalizedType.startsWith('real') ||
    normalizedType.startsWith('decimal')
  ) {
    const numeric = typeof value === 'number' ? String(value) : String(value).trim()
    if (!numeric || Number.isNaN(Number(numeric))) return null
    return `"${columnName}" = ${numeric}`
  }

  if (normalizedType === 'boolean') {
    if (typeof value === 'boolean') return `"${columnName}" = ${value ? 'true' : 'false'}`
    const lower = String(value).toLowerCase()
    if (lower === 'true' || lower === 'false') return `"${columnName}" = ${lower}`
    return null
  }

  if (normalizedType === 'date') {
    // Prefer `date 'YYYY-MM-DD'` when value looks like a date.
    const asString = String(value).slice(0, 10)
    if (/^\d{4}-\d{2}-\d{2}$/.test(asString)) {
      return `"${columnName}" = date '${asString}'`
    }
    return null
  }

  // Fallback to varchar comparison.
  return `cast("${columnName}" as varchar) = '${escapeSqlString(String(value))}'`
}

async function executeTrinoQuery(
  query: string,
  catalog: string = 'iceberg',
  schema: string = 'main',
): Promise<{
  columns: Array<string>
  columnTypes: Array<string>
  rows: Array<Record<string, unknown>>
}> {
  const trinoUrl = getTrinoUrl()

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
    throw new Error(`Trino error: ${errorText}`)
  }

  let result = await submitResponse.json()
  const allData: Array<Array<unknown>> = []
  let columns: Array<string> = []
  let columnTypes: Array<string> = []

  while (result.nextUri) {
    await new Promise((resolve) => setTimeout(resolve, 50))
    const pollResponse = await fetch(result.nextUri, {
      headers: { 'X-Trino-User': 'observatory' },
      signal: AbortSignal.timeout(30000),
    })

    if (!pollResponse.ok) {
      const errorText = await pollResponse.text()
      throw new Error(`Trino poll error: ${errorText}`)
    }

    result = await pollResponse.json()

    if (result.columns && columns.length === 0) {
      columns = result.columns.map((c: { name: string }) => c.name)
      columnTypes = result.columns.map((c: { type: string }) => c.type)
    }

    if (result.data) allData.push(...result.data)
    if (result.error) throw new Error(result.error.message || 'Query failed')
  }

  const rows = allData.map((row) => {
    const obj: Record<string, unknown> = {}
    columns.forEach((col, idx) => {
      obj[col] = row[idx]
    })
    return obj
  })

  return { columns, columnTypes, rows }
}

async function resolveIcebergTable(tableName: string): Promise<ResolveTableResult | null> {
  const safe = escapeSqlString(tableName)
  const schemasResult = await executeTrinoQuery(
    `select table_schema from iceberg.information_schema.tables where table_name = '${safe}'`,
    'iceberg',
    'main',
  )

  const schemas = schemasResult.rows
    .map((r) => String(r.table_schema))
    .filter((s) => s && s !== 'information_schema')

  if (schemas.length === 0) return null

  const preference = ['raw', 'bronze', 'silver', 'gold', 'marts', 'publish', 'main']
  schemas.sort((a, b) => preference.indexOf(a) - preference.indexOf(b))
  const schema = schemas[0] ?? 'main'

  const colsResult = await executeTrinoQuery(
    `select column_name, data_type from iceberg.information_schema.columns where table_schema = '${escapeSqlString(schema)}' and table_name = '${safe}'`,
    'iceberg',
    'main',
  )

  const columnTypes: Record<string, string> = {}
  for (const row of colsResult.rows) {
    const col = String(row.column_name)
    const typ = String(row.data_type)
    columnTypes[col] = typ
  }

  return {
    schema,
    table: tableName,
    fullName: `iceberg.${schema}.${tableName}`,
    columnTypes,
  }
}

function getTableFromAssetKey(assetKey: string): string {
  const parts = assetKey.split('/')
  return parts[parts.length - 1] || assetKey
}

const EXPLICIT_COLUMN_MAPPINGS: Record<
  string,
  Record<string, Record<string, string>>
> = {
  fct_daily_github_metrics: {
    fct_github_events: {
      activity_date: 'event_date',
      _phlo_partition_date: '_phlo_partition_date',
    },
  },
  fct_repository_languages: {
    fct_repository_stats: {
      primary_language: 'language_category',
      _phlo_partition_date: '_phlo_partition_date',
    },
  },
  mrt_github_activity_overview: {
    fct_daily_github_metrics: {
      activity_date: 'activity_date',
      _phlo_partition_date: '_phlo_partition_date',
    },
  },
  mrt_language_distribution: {
    fct_repository_languages: {
      primary_language: 'primary_language',
      _phlo_partition_date: '_phlo_partition_date',
    },
  },
  mrt_contribution_patterns: {
    fct_github_events: {
      hour_of_day: 'hour_of_day',
      day_of_week: 'day_of_week',
      _phlo_partition_date: '_phlo_partition_date',
    },
  },
}

function shouldUseAsDimension(columnName: string): boolean {
  const lower = columnName.toLowerCase()
  if (lower.startsWith('_phlo_')) return true
  if (lower.endsWith('_date')) return true
  if (lower.endsWith('_name')) return true
  if (lower.endsWith('_id')) return true
  if (lower.includes('count') || lower.includes('total') || lower.includes('avg')) return false
  if (lower.includes('score') || lower.includes('ratio') || lower.includes('pct')) return false
  if (lower.includes('rank')) return false
  if (lower.startsWith('is_')) return false
  return true
}

export const getContributingRowsQuery = createServerFn()
  .inputValidator(
    (input: {
      downstreamAssetKey: string
      upstreamAssetKey: string
      rowData: Record<string, unknown>
      limit?: number
    }) => input,
  )
  .handler(async ({ data }) => {
    const limit = data.limit ?? 100
    const upstreamTableName = getTableFromAssetKey(data.upstreamAssetKey)
    const downstreamTableName = getTableFromAssetKey(data.downstreamAssetKey)

    const upstream = await resolveIcebergTable(upstreamTableName)
    if (!upstream) {
      return { error: `Could not resolve upstream table for ${upstreamTableName}` }
    }

    const rowData = data.rowData as Record<string, Primitive>
    const upstreamCols = upstream.columnTypes

    const predicates: Array<string> = []

    const rowId = rowData._phlo_row_id
    if (rowId && upstreamCols._phlo_row_id) {
      const p = toSqlEquality('_phlo_row_id', upstreamCols._phlo_row_id, rowId)
      if (p) predicates.push(p)
    } else {
      const mappings =
        EXPLICIT_COLUMN_MAPPINGS[downstreamTableName]?.[upstreamTableName] ?? {}

      for (const [downCol, upCol] of Object.entries(mappings)) {
        const value = rowData[downCol]
        const colType = upstreamCols[upCol]
        if (!colType) continue
        const p = toSqlEquality(upCol, colType, value)
        if (p) predicates.push(p)
      }

      for (const [col, value] of Object.entries(rowData)) {
        if (!shouldUseAsDimension(col)) continue
        const colType = upstreamCols[col]
        if (!colType) continue
        const p = toSqlEquality(col, colType, value)
        if (p) predicates.push(p)
      }
    }

    const uniquePredicates = Array.from(new Set(predicates))
    if (uniquePredicates.length === 0) {
      return {
        error:
          'No safe predicates could be derived for contributing rows. Add an explicit mapping for this model pair.',
      }
    }

    const where = uniquePredicates.join(' and ')
    const query = `SELECT * FROM ${upstream.fullName} WHERE ${where} LIMIT ${limit}`

    return { query, upstream: { schema: upstream.schema, table: upstream.table } }
  })

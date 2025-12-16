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

import { quoteIdentifier } from '@/utils/sqlIdentifiers'

type Primitive = string | number | boolean | null | undefined

interface ResolveTableResult {
  schema: string
  table: string
  fullName: string
  columnTypes: Record<string, string>
}

export type ContributingRowsMode = 'entity' | 'aggregate'

const DEFAULT_CATALOG = 'iceberg'
const DEFAULT_TRINO_URL = 'http://localhost:8080'
const DEFAULT_PAGE_SIZE = 50
const MAX_PAGE_SIZE = 200
const MAX_PAGE = 200
const DEFAULT_SAMPLE_SEED = 'phlo'

function resolveTrinoUrl(override?: string): string {
  if (override && override.trim()) return override
  return process.env.TRINO_URL || DEFAULT_TRINO_URL
}

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
  if (
    normalizedType.startsWith('timestamp') ||
    normalizedType.startsWith('time')
  ) {
    const raw = String(value)
    const normalized = raw.replace(/(\.\d{1,6})$/, (match) =>
      match.padEnd(7, '0'),
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
    const numeric =
      typeof value === 'number' ? String(value) : String(value).trim()
    if (!numeric || Number.isNaN(Number(numeric))) return null
    return `"${columnName}" = ${numeric}`
  }

  if (normalizedType === 'boolean') {
    if (typeof value === 'boolean')
      return `"${columnName}" = ${value ? 'true' : 'false'}`
    const lower = String(value).toLowerCase()
    if (lower === 'true' || lower === 'false')
      return `"${columnName}" = ${lower}`
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
  options?: { trinoUrl?: string; timeoutMs?: number },
): Promise<{
  columns: Array<string>
  columnTypes: Array<string>
  rows: Array<Record<string, unknown>>
}> {
  const trinoUrl = resolveTrinoUrl(options?.trinoUrl)
  const timeoutMs = options?.timeoutMs ?? 30_000

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
      signal: AbortSignal.timeout(timeoutMs),
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

async function resolveIcebergTable(
  tableName: string,
  options?: { trinoUrl?: string; timeoutMs?: number; catalog?: string },
): Promise<ResolveTableResult | null> {
  const catalog = options?.catalog ?? DEFAULT_CATALOG
  const safe = escapeSqlString(tableName)
  const schemasResult = await executeTrinoQuery(
    `select table_schema from ${quoteIdentifier(catalog)}.information_schema.tables where table_name = '${safe}'`,
    catalog,
    'main',
    options,
  )

  const schemas = schemasResult.rows
    .map((r) => String(r.table_schema))
    .filter((s) => s && s !== 'information_schema')

  if (schemas.length === 0) return null

  const preference = [
    'raw',
    'bronze',
    'silver',
    'gold',
    'marts',
    'publish',
    'main',
  ]
  schemas.sort((a, b) => preference.indexOf(a) - preference.indexOf(b))
  const schema = schemas[0] ?? 'main'

  const colsResult = await executeTrinoQuery(
    `select column_name, data_type from ${quoteIdentifier(catalog)}.information_schema.columns where table_schema = '${escapeSqlString(schema)}' and table_name = '${safe}'`,
    catalog,
    'main',
    options,
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
    fullName: `${quoteIdentifier(catalog)}.${quoteIdentifier(schema)}.${quoteIdentifier(tableName)}`,
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
  if (
    lower.includes('count') ||
    lower.includes('total') ||
    lower.includes('avg')
  )
    return false
  if (
    lower.includes('score') ||
    lower.includes('ratio') ||
    lower.includes('pct')
  )
    return false
  if (lower.includes('rank')) return false
  if (lower.startsWith('is_')) return false
  return true
}

function toSafePageSize(pageSize: number | undefined): number {
  if (pageSize === undefined) return DEFAULT_PAGE_SIZE
  if (!Number.isFinite(pageSize)) return DEFAULT_PAGE_SIZE
  return Math.max(1, Math.min(MAX_PAGE_SIZE, Math.floor(pageSize)))
}

function toSafePage(page: number | undefined): number {
  if (page === undefined) return 0
  if (!Number.isFinite(page)) return 0
  return Math.max(0, Math.min(MAX_PAGE, Math.floor(page)))
}

function buildDeterministicOrderExpression(params: {
  columnTypes: Record<string, string>
  seed: string
}): string {
  const seedSql = escapeSqlString(params.seed)
  const columns = Object.keys(params.columnTypes)

  if (params.columnTypes._phlo_row_id) {
    return `xxhash64(to_utf8(concat('${seedSql}', '|', cast("_phlo_row_id" as varchar))))`
  }

  const orderKeyColumns = columns
    .filter((col) => {
      if (col.toLowerCase().startsWith('_phlo_')) return false
      const typ = params.columnTypes[col]?.toLowerCase() ?? ''
      return !(
        typ.startsWith('array(') ||
        typ.startsWith('map(') ||
        typ.startsWith('row(') ||
        typ.startsWith('json')
      )
    })
    .sort((a, b) => a.localeCompare(b))
    .slice(0, 5)

  if (orderKeyColumns.length === 0) {
    return `xxhash64(to_utf8('${seedSql}'))`
  }

  const concatParts = orderKeyColumns
    .map((col) => `coalesce(cast("${col}" as varchar), '')`)
    .join(", '|' , ")

  return `xxhash64(to_utf8(concat('${seedSql}', '|', ${concatParts})))`
}

export function buildContributingRowsQuery(params: {
  downstreamTableName: string
  upstream: ResolveTableResult
  rowData: Record<string, Primitive>
  pageSize: number
  page: number
  seed: string
}):
  | { ok: true; mode: ContributingRowsMode; query: string; where: string }
  | { ok: false; error: string } {
  const upstreamCols = params.upstream.columnTypes
  const predicates: Array<string> = []

  const rowId = params.rowData._phlo_row_id
  if (rowId && upstreamCols._phlo_row_id) {
    const p = toSqlEquality('_phlo_row_id', upstreamCols._phlo_row_id, rowId)
    if (p) predicates.push(p)
  } else {
    const mappings =
      EXPLICIT_COLUMN_MAPPINGS[params.downstreamTableName]?.[
        params.upstream.table
      ] ?? {}

    for (const [downCol, upCol] of Object.entries(mappings)) {
      const value = params.rowData[downCol]
      const colType = upstreamCols[upCol]
      if (!colType) continue
      const p = toSqlEquality(upCol, colType, value)
      if (p) predicates.push(p)
    }

    for (const [col, value] of Object.entries(params.rowData)) {
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
      ok: false,
      error:
        'No safe predicates could be derived for contributing rows. Add an explicit mapping for this model pair.',
    }
  }

  const where = uniquePredicates.join(' and ')
  const offset = params.page * params.pageSize
  const limitPlusOne = params.pageSize + 1

  const mode: ContributingRowsMode =
    params.rowData._phlo_row_id && upstreamCols._phlo_row_id
      ? 'entity'
      : 'aggregate'

  const orderExpr =
    mode === 'entity'
      ? `"${'_phlo_row_id'}"`
      : buildDeterministicOrderExpression({
          columnTypes: upstreamCols,
          seed: params.seed,
        })

  const query = `SELECT * FROM ${params.upstream.fullName} WHERE ${where} ORDER BY ${orderExpr} LIMIT ${limitPlusOne} OFFSET ${offset}`
  return { ok: true, mode, query, where }
}

export const getContributingRowsQuery = createServerFn()
  .inputValidator(
    (input: {
      downstreamAssetKey: string
      upstreamAssetKey: string
      rowData: Record<string, unknown>
      limit?: number
      trinoUrl?: string
      timeoutMs?: number
      catalog?: string
    }) => input,
  )
  .handler(async ({ data }) => {
    const limit = Math.max(
      1,
      Math.min(MAX_PAGE_SIZE, Math.floor(data.limit ?? 100)),
    )
    const catalog = data.catalog ?? DEFAULT_CATALOG
    const upstreamTableName = getTableFromAssetKey(data.upstreamAssetKey)
    const downstreamTableName = getTableFromAssetKey(data.downstreamAssetKey)

    const upstream = await resolveIcebergTable(upstreamTableName, {
      trinoUrl: data.trinoUrl,
      timeoutMs: data.timeoutMs,
      catalog,
    })
    if (!upstream) {
      return {
        error: `Could not resolve upstream table for ${upstreamTableName}`,
      }
    }

    const rowData = data.rowData as Record<string, Primitive>
    const built = buildContributingRowsQuery({
      downstreamTableName,
      upstream,
      rowData,
      pageSize: limit,
      page: 0,
      seed: DEFAULT_SAMPLE_SEED,
    })
    if (!built.ok) return { error: built.error }

    const query = built.query.replace(/LIMIT \d+ OFFSET \d+$/, `LIMIT ${limit}`)

    return {
      query,
      upstream: { schema: upstream.schema, table: upstream.table },
    }
  })

export const getContributingRowsPage = createServerFn()
  .inputValidator(
    (input: {
      downstreamAssetKey: string
      upstreamAssetKey: string
      rowData: Record<string, unknown>
      page?: number
      pageSize?: number
      seed?: string
      trinoUrl?: string
      timeoutMs?: number
      catalog?: string
    }) => input,
  )
  .handler(async ({ data }) => {
    const catalog = data.catalog ?? DEFAULT_CATALOG
    const upstreamTableName = getTableFromAssetKey(data.upstreamAssetKey)
    const downstreamTableName = getTableFromAssetKey(data.downstreamAssetKey)

    const upstream = await resolveIcebergTable(upstreamTableName, {
      trinoUrl: data.trinoUrl,
      timeoutMs: data.timeoutMs,
      catalog,
    })
    if (!upstream) {
      return {
        error: `Could not resolve upstream table for ${upstreamTableName}`,
      }
    }

    const pageSize = toSafePageSize(data.pageSize)
    const page = toSafePage(data.page)
    const seed =
      typeof data.seed === 'string' && data.seed.trim()
        ? data.seed.trim().slice(0, 64)
        : DEFAULT_SAMPLE_SEED

    const rowData = data.rowData as Record<string, Primitive>
    const built = buildContributingRowsQuery({
      downstreamTableName,
      upstream,
      rowData,
      pageSize,
      page,
      seed,
    })
    if (!built.ok) return { error: built.error }

    const result = await executeTrinoQuery(built.query, catalog, 'main', {
      trinoUrl: data.trinoUrl,
      timeoutMs: data.timeoutMs,
    })

    const hasMore = result.rows.length > pageSize
    const rows = hasMore ? result.rows.slice(0, pageSize) : result.rows

    return {
      mode: built.mode,
      page,
      pageSize,
      seed,
      hasMore,
      query: built.query,
      upstream: { schema: upstream.schema, table: upstream.table },
      columns: result.columns,
      columnTypes: result.columnTypes,
      rows,
    }
  })

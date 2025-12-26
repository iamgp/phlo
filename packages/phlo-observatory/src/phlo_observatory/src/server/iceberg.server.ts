/**
 * Iceberg Catalog Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

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

// Python API response types (snake_case)
interface ApiIcebergTable {
  catalog: string
  schema_name: string
  name: string
  full_name: string
  layer: 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'
}

interface ApiTableColumn {
  name: string
  type: string
  nullable: boolean
  comment?: string
}

interface ApiTableMetadata {
  table: ApiIcebergTable
  columns: Array<ApiTableColumn>
  row_count?: number
  last_modified?: string
}

// Transform Python snake_case to TypeScript camelCase
function transformTable(t: ApiIcebergTable): IcebergTable {
  return {
    catalog: t.catalog,
    schema: t.schema_name,
    name: t.name,
    fullName: t.full_name,
    layer: t.layer,
  }
}

function transformColumn(c: ApiTableColumn): TableColumn {
  return {
    name: c.name,
    type: c.type,
    nullable: c.nullable,
    comment: c.comment,
  }
}

const DEFAULT_CATALOG = 'iceberg'

/**
 * Get all tables from Iceberg catalog
 */
export const getTables = createServerFn()
  .middleware([authMiddleware])
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
      data: { branch = 'main', catalog, preferredSchema },
    }): Promise<Array<IcebergTable> | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG
      const key = cacheKeys.tables(effectiveCatalog, branch)

      return withCache(
        async () => {
          const result = await apiGet<
            Array<ApiIcebergTable> | { error: string }
          >('/api/iceberg/tables', {
            branch,
            catalog: effectiveCatalog,
            preferred_schema: preferredSchema,
          })

          if ('error' in result) {
            return result
          }

          return result.map(transformTable)
        },
        key,
        cacheTTL.tables,
      )
    },
  )

/**
 * Get table schema (columns)
 */
export const getTableSchema = createServerFn()
  .middleware([authMiddleware])
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
        async () => {
          const result = await apiGet<
            Array<ApiTableColumn> | { error: string }
          >(`/api/iceberg/tables/${encodeURIComponent(table)}/schema`, {
            branch,
            schema: effectiveSchema,
            catalog: effectiveCatalog,
          })

          if ('error' in result) {
            return result
          }

          return result.map(transformColumn)
        },
        key,
        cacheTTL.tableSchema,
      )
    },
  )

/**
 * Get row count for a table
 */
export const getTableRowCount = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { table: string; branch?: string; catalog?: string }) => input,
  )
  .handler(
    async ({
      data: { table, branch = 'main', catalog },
    }): Promise<number | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG

      return apiGet<number | { error: string }>(
        `/api/iceberg/tables/${encodeURIComponent(table)}/row-count`,
        {
          branch,
          catalog: effectiveCatalog,
        },
      )
    },
  )

/**
 * Get table metadata including schema and stats
 */
export const getTableMetadata = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { table: string; branch?: string; catalog?: string }) => input,
  )
  .handler(
    async ({
      data: { table, branch = 'main', catalog },
    }): Promise<TableMetadata | { error: string }> => {
      const effectiveCatalog = catalog ?? DEFAULT_CATALOG

      const result = await apiGet<ApiTableMetadata | { error: string }>(
        `/api/iceberg/tables/${encodeURIComponent(table)}/metadata`,
        {
          branch,
          catalog: effectiveCatalog,
        },
      )

      if ('error' in result) {
        return result
      }

      return {
        table: transformTable(result.table),
        columns: result.columns.map(transformColumn),
        rowCount: result.row_count,
        lastModified: result.last_modified,
      }
    },
  )

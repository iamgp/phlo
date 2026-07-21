/**
 * Iceberg Catalog Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/observatory/api/auth'
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

interface ApiIcebergTable {
  id: string
  name: string
  namespace?: string
  schema_name?: string
  metadata?: Record<string, unknown>
}

interface ApiBranchDetail {
  tables: Array<ApiIcebergTable>
}

function layerFromTable(t: ApiIcebergTable): IcebergTable['layer'] {
  const metadataLayer = t.metadata?.layer
  const layer =
    typeof metadataLayer === 'string'
      ? metadataLayer
      : (t.schema_name ?? t.namespace ?? '').toLowerCase()
  if (
    layer === 'bronze' ||
    layer === 'silver' ||
    layer === 'gold' ||
    layer === 'publish'
  ) {
    return layer
  }
  return 'unknown'
}

function transformTable(t: ApiIcebergTable): IcebergTable {
  const schema = t.schema_name ?? t.namespace ?? ''
  return {
    catalog: DEFAULT_CATALOG,
    schema,
    name: t.name,
    fullName: schema ? `${schema}.${t.name}` : t.id,
    layer: layerFromTable(t),
  }
}

const DEFAULT_CATALOG = 'iceberg'

/**
 * Get all tables from Iceberg catalog
 */
export const getTables = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { branch?: string } = {}) => input)
  .handler(
    async ({ data }): Promise<Array<IcebergTable> | { error: string }> => {
      const branch = data.branch?.trim() || 'main'
      const key = cacheKeys.tables(branch)

      return withCache(
        async () => {
          let result: ApiBranchDetail | { error: string }
          try {
            result = await apiGet<ApiBranchDetail | { error: string }>(
              `/api/observatory/branches/${encodeURIComponent(branch)}`,
            )
          } catch (error) {
            return {
              error:
                error instanceof Error
                  ? error.message
                  : 'Lakehouse API is unavailable',
            }
          }

          if ('error' in result) {
            return result
          }

          return result.tables.map(transformTable)
        },
        key,
        cacheTTL.tables,
      )
    },
  )

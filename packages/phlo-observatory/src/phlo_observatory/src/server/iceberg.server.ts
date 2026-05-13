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

interface ApiIcebergTable {
  catalog: string
  schema_name: string
  name: string
  full_name: string
  layer: 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'
}

function transformTable(t: ApiIcebergTable): IcebergTable {
  return {
    catalog: t.catalog,
    schema: t.schema_name,
    name: t.name,
    fullName: t.full_name,
    layer: t.layer,
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

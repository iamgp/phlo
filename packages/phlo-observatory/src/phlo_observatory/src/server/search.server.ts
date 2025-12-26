/**
 * Search Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { cacheKeys, cacheTTL, withCache } from './cache'
import type { SearchIndex, SearchIndexInput } from './search.types'
import { authMiddleware } from '@/server/auth.server'
import { apiGet } from '@/server/phlo-api'

// Python API types (snake_case)
interface ApiSearchIndex {
  assets: Array<{
    id: string
    key_path: string
    group_name?: string
    compute_kind?: string
  }>
  tables: Array<{
    catalog: string
    schema_name: string
    name: string
    full_name: string
    layer: 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'
  }>
  columns: Array<{
    table_name: string
    table_schema: string
    name: string
    type: string
  }>
  last_updated: string
}

// Transform
function transformSearchIndex(s: ApiSearchIndex): SearchIndex {
  return {
    assets: s.assets.map((a) => ({
      id: a.id,
      keyPath: a.key_path,
      groupName: a.group_name,
      computeKind: a.compute_kind,
    })),
    tables: s.tables.map((t) => ({
      catalog: t.catalog,
      schema: t.schema_name,
      name: t.name,
      fullName: t.full_name,
      layer: t.layer,
    })),
    columns: s.columns.map((c) => ({
      tableName: c.table_name,
      tableSchema: c.table_schema,
      name: c.name,
      type: c.type,
    })),
    lastUpdated: s.last_updated,
  }
}

export const getSearchIndex = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: SearchIndexInput) => input)
  .handler(
    async ({
      data: {
        dagsterUrl,
        trinoUrl,
        catalog = 'iceberg',
        branch = 'main',
        includeColumns = true,
      },
    }): Promise<SearchIndex | { error: string }> => {
      const effectiveDagsterUrl = dagsterUrl ?? ''
      const effectiveTrinoUrl = trinoUrl ?? ''
      const key = cacheKeys.searchIndex(effectiveDagsterUrl, effectiveTrinoUrl)

      return withCache(
        async () => {
          try {
            const result = await apiGet<ApiSearchIndex | { error: string }>(
              '/api/search/index',
              {
                catalog,
                branch,
                include_columns: includeColumns,
                dagster_url: effectiveDagsterUrl,
                trino_url: effectiveTrinoUrl,
              },
            )
            if ('error' in result) return result
            return transformSearchIndex(result)
          } catch (error) {
            return {
              error: error instanceof Error ? error.message : 'Unknown error',
            }
          }
        },
        key,
        cacheTTL.searchIndex,
      )
    },
  )

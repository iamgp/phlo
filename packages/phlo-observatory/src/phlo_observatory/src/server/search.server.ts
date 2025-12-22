/**
 * Search Server Functions
 *
 * Server-side function to aggregate searchable entities for the command palette.
 * Combines data from Dagster (assets) and Iceberg/Trino (tables, columns).
 */

import { createServerFn } from '@tanstack/react-start'

import { cacheKeys, cacheTTL, withCache } from './cache'
import { getAssets } from './dagster.server'
import { getTableSchema, getTables } from './iceberg.server'
import type {
  SearchIndex,
  SearchIndexInput,
  SearchableAsset,
  SearchableColumn,
  SearchableTable,
} from './search.types'
import { authMiddleware } from '@/server/auth.server'

async function buildSearchIndex(
  dagsterUrl: string | undefined,
  trinoUrl: string | undefined,
  catalog: string,
  branch: string,
  includeColumns: boolean,
): Promise<SearchIndex | { error: string }> {
  const [assetsResult, tablesResult] = await Promise.all([
    getAssets({ data: { dagsterUrl } }),
    getTables({ data: { branch, catalog, trinoUrl } }),
  ])

  if ('error' in assetsResult) {
    return { error: `Failed to fetch assets: ${assetsResult.error}` }
  }
  if ('error' in tablesResult) {
    return { error: `Failed to fetch tables: ${tablesResult.error}` }
  }

  const assets: Array<SearchableAsset> = assetsResult.map((asset) => ({
    id: asset.id,
    keyPath: asset.keyPath,
    groupName: asset.groupName,
    computeKind: asset.computeKind,
  }))

  const tables: Array<SearchableTable> = tablesResult.map((table) => ({
    catalog: table.catalog,
    schema: table.schema,
    name: table.name,
    fullName: table.fullName,
    layer: table.layer,
  }))

  let columns: Array<SearchableColumn> = []
  if (includeColumns && tables.length > 0) {
    const tablesToFetch = tables.slice(0, 20)

    const columnResults = await Promise.allSettled(
      tablesToFetch.map(async (table) => {
        const schemaResult = await getTableSchema({
          data: { table: table.name, schema: table.schema, branch, catalog },
        })

        if ('error' in schemaResult) {
          return []
        }

        return schemaResult.map((col) => ({
          tableName: table.name,
          tableSchema: table.schema,
          name: col.name,
          type: col.type,
        }))
      }),
    )

    for (const result of columnResults) {
      if (result.status === 'fulfilled') {
        columns = columns.concat(result.value)
      }
    }
  }

  return {
    assets,
    tables,
    columns,
    lastUpdated: new Date().toISOString(),
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
        () =>
          buildSearchIndex(
            dagsterUrl,
            trinoUrl,
            catalog,
            branch,
            includeColumns,
          ),
        key,
        cacheTTL.searchIndex,
      )
    },
  )

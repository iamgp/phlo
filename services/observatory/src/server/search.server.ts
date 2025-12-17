/**
 * Search Server Functions
 *
 * Server-side function to aggregate searchable entities for the command palette.
 * Combines data from Dagster (assets) and Iceberg/Trino (tables, columns).
 */

import { createServerFn } from '@tanstack/react-start'

import { getAssets } from './dagster.server'
import { getTableSchema, getTables } from './iceberg.server'
import type {
  SearchIndex,
  SearchIndexInput,
  SearchableAsset,
  SearchableColumn,
  SearchableTable,
} from './search.types'

/**
 * Build unified search index for command palette.
 *
 * Fetches assets from Dagster and tables from Iceberg, optionally including
 * column schemas. Returns a combined index for client-side fuzzy search.
 */
export const getSearchIndex = createServerFn()
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
      // Parallel fetch: assets and tables
      const [assetsResult, tablesResult] = await Promise.all([
        getAssets({ data: { dagsterUrl } }),
        getTables({
          data: { branch, catalog, trinoUrl },
        }),
      ])

      // Handle errors
      if ('error' in assetsResult) {
        return { error: `Failed to fetch assets: ${assetsResult.error}` }
      }
      if ('error' in tablesResult) {
        return { error: `Failed to fetch tables: ${tablesResult.error}` }
      }

      // Transform assets
      const assets: Array<SearchableAsset> = assetsResult.map((asset) => ({
        id: asset.id,
        keyPath: asset.keyPath,
        groupName: asset.groupName,
        computeKind: asset.computeKind,
      }))

      // Transform tables
      const tables: Array<SearchableTable> = tablesResult.map((table) => ({
        catalog: table.catalog,
        schema: table.schema,
        name: table.name,
        fullName: table.fullName,
        layer: table.layer,
      }))

      // Fetch columns if requested (progressive loading - may add latency)
      let columns: Array<SearchableColumn> = []
      if (includeColumns && tables.length > 0) {
        // Limit column fetches to avoid overwhelming Trino
        const tablesToFetch = tables.slice(0, 20)

        const columnResults = await Promise.allSettled(
          tablesToFetch.map(async (table) => {
            const schemaResult = await getTableSchema({
              data: {
                table: table.name,
                branch,
                catalog,
              },
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
    },
  )

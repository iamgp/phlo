/**
 * Dagster Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/observatory/api/auth'
import { apiGet } from '@/server/phlo-api'

// Types
interface LastMaterialization {
  timestamp: string
  runId: string
}

interface Asset {
  id: string
  key: Array<string>
  keyPath: string
  description?: string
  computeKind?: string
  groupName?: string
  lastMaterialization?: LastMaterialization
  hasMaterializePermission?: boolean
}

interface ColumnLineageDep {
  assetKey: Array<string>
  columnName: string
}

export interface AssetDetails extends Asset {
  opNames: Array<string>
  metadata: Array<{ key: string; value: string }>
  columns?: Array<{ name: string; type: string; description?: string }>
  columnLineage?: Record<string, Array<ColumnLineageDep>>
  partitionDefinition?: { description: string }
}

interface ApiAsset {
  id: string
  name: string
  description?: string
  group?: string
  kinds?: Array<string>
  metadata?: Record<string, unknown>
}

interface ApiAssetDetails {
  asset: ApiAsset
  tables?: Array<{
    metadata?: Record<string, unknown>
  }>
  column_lineage?: Record<string, Array<string>>
}

function transformAsset(a: ApiAsset): Asset {
  const key = a.id.split(/[./]/).filter(Boolean)
  const materializePermission = a.metadata?.has_materialize_permission
  const hasMaterializePermission =
    typeof materializePermission === 'boolean'
      ? materializePermission
      : undefined
  return {
    id: a.id,
    key,
    keyPath: a.id,
    description: a.description,
    computeKind: a.kinds?.[0],
    groupName: a.group,
    hasMaterializePermission,
  }
}

function transformAssetDetails(a: ApiAssetDetails): AssetDetails {
  const columns = a.tables?.flatMap((table) => {
    const metadataColumns = table.metadata?.columns
    return Array.isArray(metadataColumns)
      ? metadataColumns.filter(
          (
            column,
          ): column is { name: string; type: string; description?: string } =>
            typeof column === 'object' &&
            column !== null &&
            'name' in column &&
            typeof column.name === 'string' &&
            'type' in column &&
            typeof column.type === 'string',
        )
      : []
  })

  return {
    ...transformAsset(a.asset),
    opNames: [],
    metadata: Object.entries(a.asset.metadata ?? {}).map(([key, value]) => ({
      key,
      value: String(value),
    })),
    columns,
    columnLineage: a.column_lineage
      ? Object.fromEntries(
          Object.entries(a.column_lineage).map(([k, v]) => [
            k,
            v.map((columnName) => ({
              assetKey: a.asset.id.split(/[./]/).filter(Boolean),
              columnName,
            })),
          ]),
        )
      : undefined,
  }
}

/**
 * Get asset details
 */
export const getAssetDetails = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { assetKey: Array<string>; dagsterUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { assetKey },
    }): Promise<AssetDetails | { error: string }> => {
      try {
        const keyPath = assetKey.join('/')
        const result = await apiGet<ApiAssetDetails | { error: string }>(
          `/api/observatory/assets/${keyPath}`,
        )
        if ('error' in result) return result
        return transformAssetDetails(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

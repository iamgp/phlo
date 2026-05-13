/**
 * Dagster Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
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
  hasMaterializePermission: boolean
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
  key: Array<string>
  key_path: string
  description?: string
  compute_kind?: string
  group_name?: string
  last_materialization?: { timestamp: string; run_id: string }
  has_materialize_permission: boolean
}

interface ApiAssetDetails extends ApiAsset {
  op_names: Array<string>
  metadata: Array<{ key: string; value: string }>
  columns?: Array<{ name: string; type: string; description?: string }>
  column_lineage?: Record<
    string,
    Array<{ asset_key: Array<string>; column_name: string }>
  >
  partition_definition?: { description: string }
}

function transformAsset(a: ApiAsset): Asset {
  return {
    id: a.id,
    key: a.key,
    keyPath: a.key_path,
    description: a.description,
    computeKind: a.compute_kind,
    groupName: a.group_name,
    lastMaterialization: a.last_materialization
      ? {
          timestamp: a.last_materialization.timestamp,
          runId: a.last_materialization.run_id,
        }
      : undefined,
    hasMaterializePermission: a.has_materialize_permission,
  }
}

function transformAssetDetails(a: ApiAssetDetails): AssetDetails {
  return {
    ...transformAsset(a),
    opNames: a.op_names,
    metadata: a.metadata,
    columns: a.columns,
    columnLineage: a.column_lineage
      ? Object.fromEntries(
          Object.entries(a.column_lineage).map(([k, v]) => [
            k,
            v.map((d) => ({
              assetKey: d.asset_key,
              columnName: d.column_name,
            })),
          ]),
        )
      : undefined,
    partitionDefinition: a.partition_definition,
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
          `/api/dagster/assets/${keyPath}`,
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

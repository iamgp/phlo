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
export interface DagsterConnectionStatus {
  connected: boolean
  error?: string
  version?: string
}

export interface HealthMetrics {
  assetsTotal: number
  assetsHealthy: number
  failedJobs24h: number
  qualityChecksPassing: number
  qualityChecksTotal: number
  staleAssets: number
  lastUpdated: string
}

export interface LastMaterialization {
  timestamp: string
  runId: string
}

export interface Asset {
  id: string
  key: Array<string>
  keyPath: string
  description?: string
  computeKind?: string
  groupName?: string
  lastMaterialization?: LastMaterialization
  hasMaterializePermission: boolean
}

export interface ColumnLineageDep {
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

export interface MaterializationEvent {
  timestamp: string
  runId: string
  status: string
  stepKey?: string
  metadata: Array<{ key: string; value: string }>
  duration?: number
}

// Python API types (snake_case)
interface ApiHealthMetrics {
  assets_total: number
  assets_healthy: number
  failed_jobs_24h: number
  quality_checks_passing: number
  quality_checks_total: number
  stale_assets: number
  last_updated: string
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

interface ApiMaterialization {
  timestamp: string
  run_id: string
  status: string
  step_key?: string
  metadata: Array<{ key: string; value: string }>
  duration?: number
}

// Transform functions
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
 * Check Dagster connection
 */
export const checkDagsterConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { dagsterUrl?: string } = {}) => input)
  .handler(async (): Promise<DagsterConnectionStatus> => {
    try {
      return await apiGet<DagsterConnectionStatus>('/api/dagster/connection')
    } catch (error) {
      return {
        connected: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Get health metrics from Dagster
 */
export const getHealthMetrics = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { dagsterUrl?: string } = {}) => input)
  .handler(async (): Promise<HealthMetrics | { error: string }> => {
    try {
      const result = await apiGet<ApiHealthMetrics | { error: string }>(
        '/api/dagster/health',
      )
      if ('error' in result) return result
      return {
        assetsTotal: result.assets_total,
        assetsHealthy: result.assets_healthy,
        failedJobs24h: result.failed_jobs_24h,
        qualityChecksPassing: result.quality_checks_passing,
        qualityChecksTotal: result.quality_checks_total,
        staleAssets: result.stale_assets,
        lastUpdated: result.last_updated,
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

/**
 * Get all assets
 */
export const getAssets = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { dagsterUrl?: string } = {}) => input)
  .handler(async (): Promise<Array<Asset> | { error: string }> => {
    try {
      const result = await apiGet<Array<ApiAsset> | { error: string }>(
        '/api/dagster/assets',
      )
      if ('error' in result) return result
      return result.map(transformAsset)
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

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

/**
 * Get materialization history for an asset
 */
export const getMaterializationHistory = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { assetKey: Array<string>; limit?: number; dagsterUrl?: string }) =>
      input,
  )
  .handler(
    async ({
      data: { assetKey, limit = 20 },
    }): Promise<Array<MaterializationEvent> | { error: string }> => {
      try {
        const keyPath = assetKey.join('/')
        const result = await apiGet<
          Array<ApiMaterialization> | { error: string }
        >(`/api/dagster/assets/${keyPath}/history`, { limit })
        if ('error' in result) return result
        return result.map((m) => ({
          timestamp: m.timestamp,
          runId: m.run_id,
          status: m.status,
          stepKey: m.step_key,
          metadata: m.metadata,
          duration: m.duration,
        }))
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

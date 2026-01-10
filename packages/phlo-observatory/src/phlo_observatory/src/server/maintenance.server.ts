/**
 * Maintenance Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

export interface MaintenanceOperationStatus {
  operation: string
  namespace: string
  ref: string
  status: string
  completedAt: string
  durationSeconds?: number | null
  tablesProcessed: number
  errors: number
  snapshotsDeleted: number
  orphanFiles: number
  totalRecords: number
  totalSizeMb: number
  dryRun?: boolean | null
  runId?: string | null
  jobName?: string | null
}

export interface MaintenanceStatusSnapshot {
  lastUpdated: string
  operations: Array<MaintenanceOperationStatus>
}

interface ApiMaintenanceOperationStatus {
  operation: string
  namespace: string
  ref: string
  status: string
  completed_at: string
  duration_seconds?: number | null
  tables_processed: number
  errors: number
  snapshots_deleted: number
  orphan_files: number
  total_records: number
  total_size_mb: number
  dry_run?: boolean | null
  run_id?: string | null
  job_name?: string | null
}

interface ApiMaintenanceStatusSnapshot {
  last_updated: string
  operations: Array<ApiMaintenanceOperationStatus>
}

function transformOperation(
  operation: ApiMaintenanceOperationStatus,
): MaintenanceOperationStatus {
  return {
    operation: operation.operation,
    namespace: operation.namespace,
    ref: operation.ref,
    status: operation.status,
    completedAt: operation.completed_at,
    durationSeconds: operation.duration_seconds,
    tablesProcessed: operation.tables_processed,
    errors: operation.errors,
    snapshotsDeleted: operation.snapshots_deleted,
    orphanFiles: operation.orphan_files,
    totalRecords: operation.total_records,
    totalSizeMb: operation.total_size_mb,
    dryRun: operation.dry_run,
    runId: operation.run_id,
    jobName: operation.job_name,
  }
}

export const getMaintenanceStatus = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: Record<string, never> = {}) => input)
  .handler(async (): Promise<MaintenanceStatusSnapshot | { error: string }> => {
    try {
      const result = await withCache(
        () =>
          apiGet<ApiMaintenanceStatusSnapshot | { error: string }>(
            '/api/maintenance/status',
          ),
        cacheKeys.maintenanceStatus(),
        cacheTTL.maintenanceStatus,
      )
      if ('error' in result) return result
      return {
        lastUpdated: result.last_updated,
        operations: result.operations.map(transformOperation),
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

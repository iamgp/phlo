/**
 * Lineage Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { apiGet } from '@/server/phlo-api'

// Types
export interface RowLineageInfo {
  rowId: string
  tableName: string
  sourceType: string
  parentRowIds: Array<string>
  createdAt: string | null
}

export interface LineageJourney {
  current: RowLineageInfo | null
  ancestors: Array<RowLineageInfo>
  descendants: Array<RowLineageInfo>
}

// Python API types (snake_case)
interface ApiRowLineageInfo {
  row_id: string
  table_name: string
  source_type: string
  parent_row_ids: Array<string>
  created_at: string | null
}

interface ApiLineageJourney {
  current: ApiRowLineageInfo | null
  ancestors: Array<ApiRowLineageInfo>
  descendants: Array<ApiRowLineageInfo>
}

// Transform
function transformLineageInfo(r: ApiRowLineageInfo): RowLineageInfo {
  return {
    rowId: r.row_id,
    tableName: r.table_name,
    sourceType: r.source_type,
    parentRowIds: r.parent_row_ids,
    createdAt: r.created_at,
  }
}

/**
 * Get lineage info for a single row
 */
export const getRowLineage = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { rowId: string }) => input)
  .handler(
    async ({
      data: { rowId },
    }): Promise<RowLineageInfo | { error: string }> => {
      try {
        const result = await apiGet<ApiRowLineageInfo | { error: string }>(
          `/api/lineage/rows/${encodeURIComponent(rowId)}`,
        )
        if ('error' in result) return result
        return transformLineageInfo(result)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get all ancestor rows (recursive)
 */
export const getRowAncestors = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { rowId: string; maxDepth?: number }) => input)
  .handler(
    async ({
      data: { rowId, maxDepth = 10 },
    }): Promise<Array<RowLineageInfo> | { error: string }> => {
      try {
        const result = await apiGet<
          Array<ApiRowLineageInfo> | { error: string }
        >(`/api/lineage/rows/${encodeURIComponent(rowId)}/ancestors`, {
          max_depth: maxDepth,
        })
        if ('error' in result) return result
        return result.map(transformLineageInfo)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get all descendant rows (recursive)
 */
export const getRowDescendants = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { rowId: string; maxDepth?: number }) => input)
  .handler(
    async ({
      data: { rowId, maxDepth = 10 },
    }): Promise<Array<RowLineageInfo> | { error: string }> => {
      try {
        const result = await apiGet<
          Array<ApiRowLineageInfo> | { error: string }
        >(`/api/lineage/rows/${encodeURIComponent(rowId)}/descendants`, {
          max_depth: maxDepth,
        })
        if ('error' in result) return result
        return result.map(transformLineageInfo)
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get full lineage journey for a row (ancestors + self + descendants)
 */
export const getRowJourneyLineage = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { rowId: string }) => input)
  .handler(
    async ({
      data: { rowId },
    }): Promise<LineageJourney | { error: string }> => {
      try {
        const result = await apiGet<ApiLineageJourney | { error: string }>(
          `/api/lineage/rows/${encodeURIComponent(rowId)}/journey`,
        )
        if ('error' in result) return result
        return {
          current: result.current ? transformLineageInfo(result.current) : null,
          ancestors: result.ancestors.map(transformLineageInfo),
          descendants: result.descendants.map(transformLineageInfo),
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

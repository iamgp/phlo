/**
 * Lineage Server Functions
 *
 * Server-side functions for querying the Phlo row-level lineage store.
 * Used by the Observatory frontend to display row provenance.
 *
 * phlo-81n: Phase 3 Observatory Integration
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'

// Types for lineage data
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

// PostgreSQL connection for lineage store
const getLineageConnection = async () => {
  // Use dynamic import to avoid bundling issues
  const { Client } = await import('pg')
  const connectionString =
    process.env.PHLO_LINEAGE_DB_URL ||
    process.env.DAGSTER_PG_DB_CONNECTION_STRING ||
    'postgresql://postgres:postgres@localhost:5432/dagster'

  return new Client({ connectionString })
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
      const client = await getLineageConnection()

      try {
        await client.connect()

        const result = await client.query(
          `
          SELECT row_id, table_name, source_type, parent_row_ids,
                 created_at, metadata
          FROM phlo.row_lineage
          WHERE row_id = $1
        `,
          [rowId],
        )

        if (result.rows.length === 0) {
          return { error: `Row ${rowId} not found in lineage store` }
        }

        const row = result.rows[0]
        return {
          rowId: row.row_id,
          tableName: row.table_name,
          sourceType: row.source_type,
          parentRowIds: row.parent_row_ids || [],
          createdAt: row.created_at?.toISOString() || null,
        }
      } catch (error) {
        console.error('[getRowLineage] Error:', error)
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      } finally {
        await client.end()
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
      const client = await getLineageConnection()

      try {
        await client.connect()

        const result = await client.query(
          `
          WITH RECURSIVE ancestors AS (
            SELECT rl.row_id, rl.table_name, rl.source_type,
                   rl.parent_row_ids, rl.created_at, 1 as depth
            FROM phlo.row_lineage rl
            WHERE rl.row_id = ANY(
              SELECT unnest(parent_row_ids)
              FROM phlo.row_lineage
              WHERE row_id = $1
            )

            UNION ALL

            SELECT rl.row_id, rl.table_name, rl.source_type,
                   rl.parent_row_ids, rl.created_at, a.depth + 1
            FROM phlo.row_lineage rl
            INNER JOIN ancestors a ON rl.row_id = ANY(a.parent_row_ids)
            WHERE a.depth < $2
          )
          SELECT DISTINCT row_id, table_name, source_type,
                 parent_row_ids, created_at
          FROM ancestors
          ORDER BY created_at DESC
        `,
          [rowId, maxDepth],
        )

        return result.rows.map(
          (row: {
            row_id: string
            table_name: string
            source_type: string
            parent_row_ids: Array<string> | null
            created_at: Date | null
          }) => ({
            rowId: row.row_id,
            tableName: row.table_name,
            sourceType: row.source_type,
            parentRowIds: row.parent_row_ids || [],
            createdAt: row.created_at?.toISOString() || null,
          }),
        )
      } catch (error) {
        console.error('[getRowAncestors] Error:', error)
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      } finally {
        await client.end()
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
      const client = await getLineageConnection()

      try {
        await client.connect()

        const result = await client.query(
          `
          WITH RECURSIVE descendants AS (
            SELECT rl.row_id, rl.table_name, rl.source_type,
                   rl.parent_row_ids, rl.created_at, 1 as depth
            FROM phlo.row_lineage rl
            WHERE $1 = ANY(rl.parent_row_ids)

            UNION ALL

            SELECT rl.row_id, rl.table_name, rl.source_type,
                   rl.parent_row_ids, rl.created_at, d.depth + 1
            FROM phlo.row_lineage rl
            INNER JOIN descendants d ON d.row_id = ANY(rl.parent_row_ids)
            WHERE d.depth < $2
          )
          SELECT DISTINCT row_id, table_name, source_type,
                 parent_row_ids, created_at
          FROM descendants
          ORDER BY created_at ASC
        `,
          [rowId, maxDepth],
        )

        return result.rows.map(
          (row: {
            row_id: string
            table_name: string
            source_type: string
            parent_row_ids: Array<string> | null
            created_at: Date | null
          }) => ({
            rowId: row.row_id,
            tableName: row.table_name,
            sourceType: row.source_type,
            parentRowIds: row.parent_row_ids || [],
            createdAt: row.created_at?.toISOString() || null,
          }),
        )
      } catch (error) {
        console.error('[getRowDescendants] Error:', error)
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      } finally {
        await client.end()
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
      const client = await getLineageConnection()

      try {
        await client.connect()

        // Get current row
        const currentResult = await client.query(
          `SELECT row_id, table_name, source_type, parent_row_ids, created_at
           FROM phlo.row_lineage WHERE row_id = $1`,
          [rowId],
        )

        const current =
          currentResult.rows.length > 0
            ? {
                rowId: currentResult.rows[0].row_id,
                tableName: currentResult.rows[0].table_name,
                sourceType: currentResult.rows[0].source_type,
                parentRowIds: currentResult.rows[0].parent_row_ids || [],
                createdAt:
                  currentResult.rows[0].created_at?.toISOString() || null,
              }
            : null

        // Get ancestors (immediate parents)
        const ancestorsResult = await client.query(
          `
          SELECT rl.row_id, rl.table_name, rl.source_type, rl.parent_row_ids, rl.created_at
          FROM phlo.row_lineage rl
          WHERE rl.row_id = ANY(
            SELECT unnest(parent_row_ids)
            FROM phlo.row_lineage
            WHERE row_id = $1
          )
        `,
          [rowId],
        )

        // Get descendants (immediate children)
        const descendantsResult = await client.query(
          `
          SELECT row_id, table_name, source_type, parent_row_ids, created_at
          FROM phlo.row_lineage
          WHERE $1 = ANY(parent_row_ids)
        `,
          [rowId],
        )

        return {
          current,
          ancestors: ancestorsResult.rows.map(
            (row: {
              row_id: string
              table_name: string
              source_type: string
              parent_row_ids: Array<string> | null
              created_at: Date | null
            }) => ({
              rowId: row.row_id,
              tableName: row.table_name,
              sourceType: row.source_type,
              parentRowIds: row.parent_row_ids || [],
              createdAt: row.created_at?.toISOString() || null,
            }),
          ),
          descendants: descendantsResult.rows.map(
            (row: {
              row_id: string
              table_name: string
              source_type: string
              parent_row_ids: Array<string> | null
              created_at: Date | null
            }) => ({
              rowId: row.row_id,
              tableName: row.table_name,
              sourceType: row.source_type,
              parentRowIds: row.parent_row_ids || [],
              createdAt: row.created_at?.toISOString() || null,
            }),
          ),
        }
      } catch (error) {
        console.error('[getRowJourneyLineage] Error:', error)
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      } finally {
        await client.end()
      }
    },
  )

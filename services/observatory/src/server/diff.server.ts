/**
 * Stage Diff Server Functions
 *
 * Computes diffs between pipeline stages by analyzing SQL transformations
 * and comparing schema/column changes.
 */

import { createServerFn } from '@tanstack/react-start'

import type { ColumnMapping, TransformType } from '@/utils/sqlParser'
import { analyzeSQLTransformation } from '@/utils/sqlParser'

/**
 * Column change type for diff display
 */
export type ColumnChangeType =
  | 'added'
  | 'removed'
  | 'renamed'
  | 'transformed'
  | 'unchanged'

/**
 * Column diff entry
 */
export interface ColumnDiff {
  column: string
  changeType: ColumnChangeType
  sourceColumn?: string
  transformation?: string
}

/**
 * Aggregation info extracted from SQL
 */
export interface AggregationInfo {
  groupBy: Array<string>
  aggregates: Array<{ expression: string; alias: string }>
}

/**
 * Full stage diff result
 */
export interface StageDiffResult {
  transformType: TransformType
  confidence: number
  confidenceReasons: Array<string>
  columnDiffs: Array<ColumnDiff>
  aggregation?: AggregationInfo
  sourceTables: Array<string>
  summary: {
    addedCount: number
    removedCount: number
    renamedCount: number
    transformedCount: number
    unchangedCount: number
  }
}

/**
 * Extract GROUP BY columns from SQL
 */
function extractGroupByColumns(sql: string): Array<string> {
  const match = sql.match(/GROUP\s+BY\s+([^)]+?)(?:HAVING|ORDER|LIMIT|$)/is)
  if (!match) return []

  const groupByClause = match[1]
  // Split by commas, handling nested parentheses
  const columns: Array<string> = []
  let current = ''
  let depth = 0

  for (const char of groupByClause) {
    if (char === '(') depth++
    if (char === ')') depth--

    if (char === ',' && depth === 0) {
      const col = current.trim()
      if (col) columns.push(col)
      current = ''
    } else {
      current += char
    }
  }

  const lastCol = current.trim()
  if (lastCol) columns.push(lastCol)

  return columns.map((c) => {
    // Extract just the column name (remove table aliases, etc.)
    const parts = c.split('.')
    return parts[parts.length - 1].replace(/"/g, '').trim()
  })
}

/**
 * Extract aggregate expressions from column mappings
 */
function extractAggregates(
  mappings: Array<ColumnMapping>,
): Array<{ expression: string; alias: string }> {
  const aggregateFunctions = [
    'COUNT',
    'SUM',
    'AVG',
    'MIN',
    'MAX',
    'ARRAY_AGG',
    'STRING_AGG',
  ]

  return mappings
    .filter((m) => {
      const upperExpr = m.sourceExpression.toUpperCase()
      return aggregateFunctions.some((fn) => upperExpr.includes(`${fn}(`))
    })
    .map((m) => ({
      expression: m.sourceExpression,
      alias: m.targetColumn,
    }))
}

/**
 * Compute column diffs between upstream and downstream
 */
function computeColumnDiffs(
  upstreamColumns: Array<string>,
  downstreamColumns: Array<string>,
  mappings: Array<ColumnMapping>,
): Array<ColumnDiff> {
  const diffs: Array<ColumnDiff> = []
  const upstreamSet = new Set(upstreamColumns.map((c) => c.toLowerCase()))
  const downstreamSet = new Set(downstreamColumns.map((c) => c.toLowerCase()))
  const processedDownstream = new Set<string>()

  // Check each downstream column
  for (const downCol of downstreamColumns) {
    const lowerDown = downCol.toLowerCase()

    // Find if there's a mapping for this column
    const mapping = mappings.find(
      (m) => m.targetColumn.toLowerCase() === lowerDown,
    )

    if (mapping) {
      const sourceCol = mapping.sourceColumn?.toLowerCase()

      if (sourceCol && upstreamSet.has(sourceCol)) {
        // Check if it's a direct match (unchanged) or transformed
        if (sourceCol === lowerDown && !mapping.transformation) {
          diffs.push({
            column: downCol,
            changeType: 'unchanged',
            sourceColumn: mapping.sourceColumn,
          })
        } else if (sourceCol !== lowerDown) {
          // Renamed (possibly with transformation)
          diffs.push({
            column: downCol,
            changeType: 'renamed',
            sourceColumn: mapping.sourceColumn,
            transformation: mapping.transformation,
          })
        } else if (mapping.transformation) {
          // Same name but transformed
          diffs.push({
            column: downCol,
            changeType: 'transformed',
            sourceColumn: mapping.sourceColumn,
            transformation: mapping.transformation,
          })
        }
      } else {
        // Source column doesn't exist upstream or is an aggregate - it's added
        diffs.push({
          column: downCol,
          changeType: 'added',
          transformation: mapping.transformation,
        })
      }
    } else {
      // No mapping found
      if (upstreamSet.has(lowerDown)) {
        // Column exists in both with same name - unchanged
        diffs.push({
          column: downCol,
          changeType: 'unchanged',
          sourceColumn: downCol,
        })
      } else {
        // Doesn't exist upstream - added
        diffs.push({
          column: downCol,
          changeType: 'added',
        })
      }
    }

    processedDownstream.add(lowerDown)
  }

  // Check for removed columns (in upstream but not in downstream)
  for (const upCol of upstreamColumns) {
    const lowerUp = upCol.toLowerCase()
    if (!downstreamSet.has(lowerUp)) {
      // Check if it was renamed
      const wasRenamed = diffs.some(
        (d) =>
          d.changeType === 'renamed' &&
          d.sourceColumn?.toLowerCase() === lowerUp,
      )

      if (!wasRenamed) {
        diffs.push({
          column: upCol,
          changeType: 'removed',
        })
      }
    }
  }

  return diffs
}

/**
 * Get stage diff by analyzing transformation SQL
 *
 * This analyzes the downstream's SQL to understand how it transforms
 * data from the upstream table.
 */
export const getStageDiff = createServerFn()
  .inputValidator(
    (input: {
      transformationSql: string
      upstreamColumns: Array<string>
      downstreamColumns: Array<string>
    }) => input,
  )
  .handler(async ({ data }): Promise<StageDiffResult> => {
    const { transformationSql, upstreamColumns, downstreamColumns } = data

    // Analyze the SQL
    const analysis = analyzeSQLTransformation(transformationSql)

    // Compute column diffs
    const columnDiffs = computeColumnDiffs(
      upstreamColumns,
      downstreamColumns,
      analysis.columnMappings,
    )

    // Extract aggregation info if present
    let aggregation: AggregationInfo | undefined
    if (analysis.hasGroupBy || analysis.hasAggregates) {
      const groupBy = extractGroupByColumns(transformationSql)
      const aggregates = extractAggregates(analysis.columnMappings)

      if (groupBy.length > 0 || aggregates.length > 0) {
        aggregation = { groupBy, aggregates }
      }
    }

    // Compute summary
    const summary = {
      addedCount: columnDiffs.filter((d) => d.changeType === 'added').length,
      removedCount: columnDiffs.filter((d) => d.changeType === 'removed')
        .length,
      renamedCount: columnDiffs.filter((d) => d.changeType === 'renamed')
        .length,
      transformedCount: columnDiffs.filter(
        (d) => d.changeType === 'transformed',
      ).length,
      unchangedCount: columnDiffs.filter((d) => d.changeType === 'unchanged')
        .length,
    }

    return {
      transformType: analysis.transformType,
      confidence: analysis.confidence,
      confidenceReasons: analysis.confidenceReasons,
      columnDiffs,
      aggregation,
      sourceTables: analysis.sourceTables,
      summary,
    }
  })

/**
 * Simple diff computation without SQL analysis
 * Used when transformation SQL is not available
 */
export const getSimpleStageDiff = createServerFn()
  .inputValidator(
    (input: { upstreamColumns: Array<string>; downstreamColumns: Array<string> }) =>
      input,
  )
  .handler(async ({ data }): Promise<StageDiffResult> => {
    const { upstreamColumns, downstreamColumns } = data

    const upstreamSet = new Set(upstreamColumns.map((c) => c.toLowerCase()))
    const downstreamSet = new Set(downstreamColumns.map((c) => c.toLowerCase()))

    const columnDiffs: Array<ColumnDiff> = []

    // Added columns
    for (const col of downstreamColumns) {
      if (!upstreamSet.has(col.toLowerCase())) {
        columnDiffs.push({ column: col, changeType: 'added' })
      } else {
        columnDiffs.push({
          column: col,
          changeType: 'unchanged',
          sourceColumn: col,
        })
      }
    }

    // Removed columns
    for (const col of upstreamColumns) {
      if (!downstreamSet.has(col.toLowerCase())) {
        columnDiffs.push({ column: col, changeType: 'removed' })
      }
    }

    const summary = {
      addedCount: columnDiffs.filter((d) => d.changeType === 'added').length,
      removedCount: columnDiffs.filter((d) => d.changeType === 'removed')
        .length,
      renamedCount: 0,
      transformedCount: 0,
      unchangedCount: columnDiffs.filter((d) => d.changeType === 'unchanged')
        .length,
    }

    return {
      transformType: 'ONE_TO_ONE',
      confidence: 50,
      confidenceReasons: ['No SQL available - column comparison only'],
      columnDiffs,
      sourceTables: [],
      summary,
    }
  })

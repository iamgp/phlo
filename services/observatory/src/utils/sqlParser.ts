/**
 * SQL Parser Utilities
 *
 * Parse transformation SQL to understand column mappings and build reverse queries
 * for tracing data through the pipeline.
 */

export interface ColumnMapping {
  targetColumn: string // Column name in the output (e.g., "activity_date")
  sourceExpression: string // Original expression (e.g., "DATE(created_at)")
  sourceColumn?: string // Base column name if extractable (e.g., "created_at")
  transformation?: string // Function applied (e.g., "DATE")
}

export interface SQLAnalysis {
  columnMappings: Array<ColumnMapping>
  sourceTables: Array<string>
  joinConditions?: Array<string>
  whereConditions?: Array<string>
}

/**
 * Parse SQL to extract column mappings from SELECT clause
 */
export function parseColumnMappings(sql: string): Array<ColumnMapping> {
  const mappings: Array<ColumnMapping> = []

  // Extract SELECT clause (basic approach)
  const selectMatch = sql.match(/SELECT\s+(.*?)\s+FROM/is)
  if (!selectMatch) return mappings

  const selectClause = selectMatch[1]

  // Split by commas (handle nested functions)
  const columns = splitSelectColumns(selectClause)

  for (const col of columns) {
    const trimmed = col.trim()

    // Check for alias (AS keyword)
    const asMatch = trimmed.match(/^(.*?)\s+AS\s+(\w+)$/i)
    if (asMatch) {
      const sourceExpr = asMatch[1].trim()
      const targetCol = asMatch[2].trim()

      mappings.push({
        targetColumn: targetCol,
        sourceExpression: sourceExpr,
        sourceColumn: extractBaseColumn(sourceExpr),
        transformation: extractTransformation(sourceExpr),
      })
      continue
    }

    // Check for alias (space without AS)
    const spaceMatch = trimmed.match(/^(.*?)\s+(\w+)$/)
    if (spaceMatch && !isKeyword(spaceMatch[2])) {
      const sourceExpr = spaceMatch[1].trim()
      const targetCol = spaceMatch[2].trim()

      mappings.push({
        targetColumn: targetCol,
        sourceExpression: sourceExpr,
        sourceColumn: extractBaseColumn(sourceExpr),
        transformation: extractTransformation(sourceExpr),
      })
      continue
    }

    // No alias - column name is same as source
    const baseCol = extractBaseColumn(trimmed)
    if (baseCol) {
      mappings.push({
        targetColumn: baseCol,
        sourceExpression: trimmed,
        sourceColumn: baseCol,
      })
    }
  }

  return mappings
}

/**
 * Split SELECT columns handling nested parentheses
 */
function splitSelectColumns(selectClause: string): Array<string> {
  const columns: Array<string> = []
  let current = ''
  let depth = 0

  for (const char of selectClause) {
    if (char === '(') depth++
    if (char === ')') depth--

    if (char === ',' && depth === 0) {
      columns.push(current)
      current = ''
    } else {
      current += char
    }
  }

  if (current.trim()) {
    columns.push(current)
  }

  return columns
}

/**
 * Extract the base column name from an expression
 * Examples:
 *   "DATE(created_at)" -> "created_at"
 *   "COUNT(*)" -> null
 *   "user_id" -> "user_id"
 *   "CAST(amount AS DECIMAL)" -> "amount"
 */
function extractBaseColumn(expr: string): string | undefined {
  // Remove whitespace
  const trimmed = expr.trim()

  // Check for simple column name (no functions)
  if (/^\w+$/.test(trimmed)) {
    return trimmed
  }

  // Extract from function calls - look for column names in parentheses
  // Match patterns like FUNC(column) or FUNC(table.column)
  const funcMatch = trimmed.match(/\w+\(([\w.]+)/)
  if (funcMatch) {
    const colName = funcMatch[1]
    // If it has a dot, take the part after the dot
    if (colName.includes('.')) {
      return colName.split('.')[1]
    }
    // Skip special keywords
    if (colName !== '*' && !isKeyword(colName)) {
      return colName
    }
  }

  // Try to find any column-like identifier
  const identMatch = trimmed.match(/(\w+\.\w+|\w+)/)
  if (identMatch) {
    const ident = identMatch[1]
    if (ident.includes('.')) {
      return ident.split('.')[1]
    }
    if (!isKeyword(ident) && ident !== '*') {
      return ident
    }
  }

  return undefined
}

/**
 * Extract transformation function from expression
 */
function extractTransformation(expr: string): string | undefined {
  const funcMatch = expr.match(/^(\w+)\(/)
  return funcMatch ? funcMatch[1] : undefined
}

/**
 * Check if a word is a SQL keyword
 */
function isKeyword(word: string): boolean {
  const keywords = [
    'SELECT',
    'FROM',
    'WHERE',
    'JOIN',
    'LEFT',
    'RIGHT',
    'INNER',
    'OUTER',
    'ON',
    'AND',
    'OR',
    'NOT',
    'NULL',
    'AS',
    'DISTINCT',
    'GROUP',
    'ORDER',
    'BY',
    'HAVING',
    'LIMIT',
    'OFFSET',
  ]
  return keywords.includes(word.toUpperCase())
}

/**
 * Extract source table names from SQL
 */
export function extractSourceTables(sql: string): Array<string> {
  const tables: Array<string> = []

  // Extract FROM clause
  const fromMatch = sql.match(/FROM\s+(\w+)/i)
  if (fromMatch) {
    tables.push(fromMatch[1])
  }

  // Extract JOIN clauses
  const joinMatches = sql.matchAll(/JOIN\s+(\w+)/gi)
  for (const match of joinMatches) {
    tables.push(match[1])
  }

  return tables
}

/**
 * Build a WHERE clause to query upstream table based on downstream row data
 */
export function buildUpstreamWhereClause(
  downstreamRow: Record<string, unknown>,
  columnMappings: Array<ColumnMapping>,
): string {
  const conditions: Array<string> = []

  for (const [downstreamCol, value] of Object.entries(downstreamRow)) {
    // Find the mapping for this column
    const mapping = columnMappings.find((m) => m.targetColumn === downstreamCol)
    if (!mapping || !mapping.sourceColumn) continue

    // Skip aggregate functions (can't reverse them)
    if (
      mapping.transformation &&
      ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX'].includes(
        mapping.transformation.toUpperCase(),
      )
    ) {
      continue
    }

    // Build condition based on transformation
    if (mapping.transformation) {
      const func = mapping.transformation.toUpperCase()

      if (func === 'DATE' || func === 'DATE_TRUNC') {
        // For DATE transformations, query with date range
        if (typeof value === 'string') {
          conditions.push(`DATE(${mapping.sourceColumn}) = DATE '${value}'`)
        }
      } else if (func === 'CAST') {
        // For CAST, use original column
        if (value === null || value === undefined) {
          conditions.push(`${mapping.sourceColumn} IS NULL`)
        } else if (typeof value === 'string') {
          conditions.push(
            `${mapping.sourceColumn} = '${value.replace(/'/g, "''")}'`,
          )
        } else {
          conditions.push(`${mapping.sourceColumn} = ${value}`)
        }
      } else {
        // For other functions, try to match with the function applied
        if (value === null || value === undefined) {
          conditions.push(`${mapping.sourceExpression} IS NULL`)
        } else if (typeof value === 'string') {
          conditions.push(
            `${mapping.sourceExpression} = '${value.replace(/'/g, "''")}'`,
          )
        } else {
          conditions.push(`${mapping.sourceExpression} = ${value}`)
        }
      }
    } else {
      // No transformation - direct column mapping
      if (value === null || value === undefined) {
        conditions.push(`${mapping.sourceColumn} IS NULL`)
      } else if (typeof value === 'string') {
        conditions.push(
          `${mapping.sourceColumn} = '${value.replace(/'/g, "''")}'`,
        )
      } else if (typeof value === 'number') {
        conditions.push(`${mapping.sourceColumn} = ${value}`)
      } else if (typeof value === 'boolean') {
        conditions.push(`${mapping.sourceColumn} = ${value}`)
      }
    }
  }

  return conditions.join(' AND ')
}

/**
 * Analyze SQL to extract full transformation information
 */
export function analyzeSQLTransformation(sql: string): SQLAnalysis {
  return {
    columnMappings: parseColumnMappings(sql),
    sourceTables: extractSourceTables(sql),
  }
}

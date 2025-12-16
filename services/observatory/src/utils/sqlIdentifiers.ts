export function quoteIdentifier(identifier: string): string {
  const escaped = identifier.replaceAll('"', '""')
  return `"${escaped}"`
}

export function isProbablyQualifiedTable(table: string): boolean {
  const trimmed = table.trim()
  return trimmed.includes('.') || trimmed.includes('"')
}

export function qualifyTableName(params: {
  catalog: string
  schema: string
  table: string
}): string {
  const { catalog, schema, table } = params
  return `${quoteIdentifier(catalog)}.${quoteIdentifier(schema)}.${quoteIdentifier(table)}`
}

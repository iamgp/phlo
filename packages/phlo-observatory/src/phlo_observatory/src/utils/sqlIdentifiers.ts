export function quoteIdentifier(identifier: string): string {
  const escaped = identifier.replaceAll('"', '""')
  return `"${escaped}"`
}

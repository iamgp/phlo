/**
 * Search Types
 *
 * Type definitions for the command palette search index.
 */

/** Searchable asset from Dagster */
export interface SearchableAsset {
  id: string
  keyPath: string
  groupName?: string
  computeKind?: string
}

/** Searchable table from Iceberg catalog */
export interface SearchableTable {
  catalog: string
  schema: string
  name: string
  fullName: string
  layer: 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'
}

/** Searchable column from table schema */
export interface SearchableColumn {
  tableName: string
  tableSchema: string
  name: string
  type: string
}

/** Unified search index for command palette */
export interface SearchIndex {
  assets: Array<SearchableAsset>
  tables: Array<SearchableTable>
  columns: Array<SearchableColumn>
  lastUpdated: string
}

/** Input for getSearchIndex server function */
export interface SearchIndexInput {
  dagsterUrl?: string
  trinoUrl?: string
  catalog?: string
  branch?: string
  includeColumns?: boolean
}

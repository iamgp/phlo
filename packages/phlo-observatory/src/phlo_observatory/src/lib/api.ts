/**
 * Observatory API Client
 *
 * Centralized client for calling the Python phlo-api backend.
 * Replaces TanStack Start server functions with fetch calls.
 */

// API base URL - phlo-api runs alongside Observatory
const API_BASE = '/api'

/**
 * Make a GET request to the API
 */
async function apiGet<T>(
  endpoint: string,
  params?: Record<string, string | number | boolean | undefined>,
): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const response = await fetch(url.toString())
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

/**
 * Make a POST request to the API
 */
async function apiPost<T>(endpoint: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

/**
 * Make a DELETE request to the API
 */
async function apiDelete<T>(
  endpoint: string,
  params?: Record<string, string>,
): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value)
    }
  }
  const response = await fetch(url.toString(), { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

// ============================================================================
// Trino API
// ============================================================================

export interface DataRow {
  [key: string]: string | number | boolean | null | undefined
}

export interface DataPreviewResult {
  columns: Array<string>
  column_types: Array<string>
  rows: Array<DataRow>
  total_rows?: number
  has_more: boolean
}

export interface TrinoConnectionStatus {
  connected: boolean
  error?: string
  cluster_version?: string
}

export interface ColumnProfile {
  column: string
  type: string
  null_count: number
  null_percentage: number
  distinct_count: number
  min_value?: string
  max_value?: string
}

export interface TableMetrics {
  row_count: number
  size_bytes?: number
}

export const trinoApi = {
  checkConnection: (trinoUrl?: string) =>
    apiGet<TrinoConnectionStatus>('/trino/connection', { trino_url: trinoUrl }),

  previewData: (
    table: string,
    options?: {
      branch?: string
      catalog?: string
      schema?: string
      limit?: number
      offset?: number
    },
  ) =>
    apiGet<DataPreviewResult | { error: string }>(
      `/trino/preview/${encodeURIComponent(table)}`,
      {
        branch: options?.branch,
        catalog: options?.catalog,
        schema: options?.schema,
        limit: options?.limit,
        offset: options?.offset,
      },
    ),

  profileColumn: (
    table: string,
    column: string,
    options?: {
      branch?: string
      catalog?: string
    },
  ) =>
    apiGet<ColumnProfile | { error: string }>(
      `/trino/profile/${encodeURIComponent(table)}/${encodeURIComponent(column)}`,
      {
        branch: options?.branch,
        catalog: options?.catalog,
      },
    ),

  getTableMetrics: (table: string, options?: { branch?: string }) =>
    apiGet<TableMetrics | { error: string }>(
      `/trino/metrics/${encodeURIComponent(table)}`,
      {
        branch: options?.branch,
      },
    ),

  executeQuery: (
    query: string,
    options?: {
      branch?: string
      catalog?: string
      read_only_mode?: boolean
    },
  ) =>
    apiPost<DataPreviewResult | { error: string; kind: string }>(
      '/trino/query',
      {
        query,
        branch: options?.branch,
        catalog: options?.catalog,
        read_only_mode: options?.read_only_mode ?? true,
      },
    ),

  getRowById: (table: string, rowId: string) =>
    apiGet<DataPreviewResult | { error: string }>(
      `/trino/row/${encodeURIComponent(table)}/${encodeURIComponent(rowId)}`,
    ),
}

// ============================================================================
// Iceberg API
// ============================================================================

export type Layer = 'bronze' | 'silver' | 'gold' | 'publish' | 'unknown'

export interface IcebergTable {
  catalog: string
  schema_name: string
  name: string
  full_name: string
  layer: Layer
}

export interface TableColumn {
  name: string
  type: string
  nullable: boolean
  comment?: string
}

export interface TableMetadata {
  table: IcebergTable
  columns: Array<TableColumn>
  row_count?: number
}

export const icebergApi = {
  getTables: (options?: { branch?: string; catalog?: string }) =>
    apiGet<Array<IcebergTable> | { error: string }>('/iceberg/tables', {
      branch: options?.branch,
      catalog: options?.catalog,
    }),

  getTableSchema: (
    table: string,
    options?: { branch?: string; schema?: string },
  ) =>
    apiGet<Array<TableColumn> | { error: string }>(
      `/iceberg/tables/${encodeURIComponent(table)}/schema`,
      {
        branch: options?.branch,
        schema: options?.schema,
      },
    ),

  getTableMetadata: (table: string, options?: { branch?: string }) =>
    apiGet<TableMetadata | { error: string }>(
      `/iceberg/tables/${encodeURIComponent(table)}/metadata`,
      {
        branch: options?.branch,
      },
    ),

  getTableRowCount: (table: string, options?: { branch?: string }) =>
    apiGet<number | { error: string }>(
      `/iceberg/tables/${encodeURIComponent(table)}/row-count`,
      {
        branch: options?.branch,
      },
    ),
}

// ============================================================================
// Dagster API
// ============================================================================

export interface DagsterConnectionStatus {
  connected: boolean
  error?: string
  version?: string
}

export interface HealthMetrics {
  assets_total: number
  assets_healthy: number
  failed_jobs_24h: number
  quality_checks_passing: number
  quality_checks_total: number
  stale_assets: number
  last_updated: string
}

export interface Asset {
  id: string
  key: Array<string>
  key_path: string
  description?: string
  compute_kind?: string
  group_name?: string
  last_materialization?: {
    timestamp: string
    run_id: string
  }
  has_materialize_permission: boolean
}

export interface AssetDetails extends Asset {
  op_names: Array<string>
  metadata: Array<{ key: string; value: string }>
  columns?: Array<{ name: string; type: string; description?: string }>
  column_lineage?: Record<
    string,
    Array<{ asset_key: Array<string>; column_name: string }>
  >
  partition_definition?: { description: string }
}

export interface MaterializationEvent {
  timestamp: string
  run_id: string
  status: string
  step_key?: string
  metadata: Array<{ key: string; value: string }>
}

export const dagsterApi = {
  checkConnection: () => apiGet<DagsterConnectionStatus>('/dagster/connection'),

  getHealthMetrics: () =>
    apiGet<HealthMetrics | { error: string }>('/dagster/health'),

  getAssets: () => apiGet<Array<Asset> | { error: string }>('/dagster/assets'),

  getAssetDetails: (assetKeyPath: string) =>
    apiGet<AssetDetails | { error: string }>(`/dagster/assets/${assetKeyPath}`),

  getMaterializationHistory: (assetKeyPath: string, limit?: number) =>
    apiGet<Array<MaterializationEvent> | { error: string }>(
      `/dagster/assets/${assetKeyPath}/history`,
      { limit },
    ),
}

// ============================================================================
// Nessie API
// ============================================================================

export interface Branch {
  type: 'BRANCH' | 'TAG'
  name: string
  hash: string
}

export interface CommitMeta {
  hash: string
  message: string
  committer?: string
  authors: Array<string>
  commit_time?: string
}

export interface LogEntry {
  commit_meta: CommitMeta
  parent_commit_hash?: string
}

export interface NessieConnectionStatus {
  connected: boolean
  error?: string
  default_branch?: string
}

export const nessieApi = {
  checkConnection: () => apiGet<NessieConnectionStatus>('/nessie/connection'),

  getBranches: () =>
    apiGet<Array<Branch> | { error: string }>('/nessie/branches'),

  getBranch: (name: string) =>
    apiGet<Branch | { error: string }>(
      `/nessie/branches/${encodeURIComponent(name)}`,
    ),

  getCommits: (branch: string, limit?: number) =>
    apiGet<Array<LogEntry> | { error: string }>(
      `/nessie/branches/${encodeURIComponent(branch)}/history`,
      { limit },
    ),

  getContents: (branch: string, prefix?: string) =>
    apiGet<Array<unknown> | { error: string }>(
      `/nessie/branches/${encodeURIComponent(branch)}/entries`,
      { prefix },
    ),

  compareBranches: (fromBranch: string, toBranch: string) =>
    apiGet<unknown>(
      `/nessie/diff/${encodeURIComponent(fromBranch)}/${encodeURIComponent(toBranch)}`,
    ),

  createBranch: (name: string, fromBranch: string) =>
    apiPost<Branch | { error: string }>('/nessie/branches', {
      name,
      from_branch: fromBranch,
    }),

  deleteBranch: (name: string, expectedHash: string) =>
    apiDelete<{ success: boolean } | { error: string }>(
      `/nessie/branches/${encodeURIComponent(name)}`,
      {
        expected_hash: expectedHash,
      },
    ),

  mergeBranch: (fromBranch: string, intoBranch: string, message?: string) =>
    apiPost<{ success: boolean; hash?: string } | { error: string }>(
      '/nessie/merge',
      {
        from_branch: fromBranch,
        into_branch: intoBranch,
        message,
      },
    ),
}

// ============================================================================
// Quality API
// ============================================================================

export interface QualityCheck {
  name: string
  asset_key: Array<string>
  description?: string
  severity: 'WARN' | 'ERROR'
  status: 'PASSED' | 'FAILED' | 'IN_PROGRESS' | 'SKIPPED'
  last_execution_time?: string
  last_result?: {
    passed: boolean
    metadata: Record<string, unknown>
  }
}

export interface QualityOverview {
  total_checks: number
  passing_checks: number
  failing_checks: number
  warning_checks: number
  quality_score: number
  by_category: Array<{
    category: string
    passing: number
    total: number
    percentage: number
  }>
}

export interface CheckExecution {
  timestamp: string
  passed: boolean
  run_id?: string
  metadata: Record<string, unknown>
}

export const qualityApi = {
  getOverview: () =>
    apiGet<QualityOverview | { error: string }>('/quality/overview'),

  getAssetChecks: (assetKeyPath: string) =>
    apiGet<Array<QualityCheck> | { error: string }>(
      `/quality/assets/${assetKeyPath}/checks`,
    ),

  getCheckHistory: (assetKeyPath: string, checkName: string, limit?: number) =>
    apiGet<Array<CheckExecution> | { error: string }>(
      `/quality/assets/${assetKeyPath}/checks/${encodeURIComponent(checkName)}/history`,
      { limit },
    ),

  getFailingChecks: () =>
    apiGet<Array<QualityCheck> | { error: string }>('/quality/failing'),
}

// ============================================================================
// Loki API
// ============================================================================

export interface LokiLogEntry {
  timestamp: string
  level: 'debug' | 'info' | 'warn' | 'error'
  message: string
  metadata: Record<string, string>
}

export interface LogQueryResult {
  entries: Array<LokiLogEntry>
  has_more: boolean
}

export interface LokiConnectionStatus {
  connected: boolean
  error?: string
  version?: string
}

export const lokiApi = {
  checkConnection: () => apiGet<LokiConnectionStatus>('/loki/connection'),

  queryLogs: (options: {
    start: string
    end: string
    run_id?: string
    asset_key?: string
    job?: string
    level?: string
    limit?: number
  }) => apiGet<LogQueryResult | { error: string }>('/loki/query', options),

  queryRunLogs: (runId: string, limit?: number) =>
    apiGet<LogQueryResult | { error: string }>(
      `/loki/runs/${encodeURIComponent(runId)}`,
      { limit },
    ),

  queryAssetLogs: (
    assetKey: string,
    options?: { partition_key?: string; hours_back?: number; limit?: number },
  ) =>
    apiGet<LogQueryResult | { error: string }>(
      `/loki/assets/${assetKey}`,
      options,
    ),

  getLabels: () =>
    apiGet<{ labels: Array<string> } | { error: string }>('/loki/labels'),
}

// ============================================================================
// Lineage API
// ============================================================================

export interface RowLineageInfo {
  row_id: string
  table_name: string
  source_type: string
  parent_row_ids: Array<string>
  created_at?: string
}

export interface LineageJourney {
  current: RowLineageInfo | null
  ancestors: Array<RowLineageInfo>
  descendants: Array<RowLineageInfo>
}

export const lineageApi = {
  getRowLineage: (rowId: string) =>
    apiGet<RowLineageInfo | { error: string }>(
      `/lineage/rows/${encodeURIComponent(rowId)}`,
    ),

  getRowAncestors: (rowId: string, maxDepth?: number) =>
    apiGet<Array<RowLineageInfo> | { error: string }>(
      `/lineage/rows/${encodeURIComponent(rowId)}/ancestors`,
      { max_depth: maxDepth },
    ),

  getRowDescendants: (rowId: string, maxDepth?: number) =>
    apiGet<Array<RowLineageInfo> | { error: string }>(
      `/lineage/rows/${encodeURIComponent(rowId)}/descendants`,
      { max_depth: maxDepth },
    ),

  getRowJourney: (rowId: string) =>
    apiGet<LineageJourney | { error: string }>(
      `/lineage/rows/${encodeURIComponent(rowId)}/journey`,
    ),
}

// ============================================================================
// Search API
// ============================================================================

export interface SearchIndex {
  assets: Array<{
    id: string
    key_path: string
    group_name?: string
    compute_kind?: string
  }>
  tables: Array<{
    catalog: string
    schema_name: string
    name: string
    full_name: string
    layer: string
  }>
  columns: Array<{
    table_name: string
    table_schema: string
    name: string
    type: string
  }>
  last_updated: string
}

export const searchApi = {
  getSearchIndex: (options?: { include_columns?: boolean }) =>
    apiGet<SearchIndex | { error: string }>('/search/index', options),
}

// ============================================================================
// Unified API export
// ============================================================================

export const api = {
  trino: trinoApi,
  iceberg: icebergApi,
  dagster: dagsterApi,
  nessie: nessieApi,
  quality: qualityApi,
  loki: lokiApi,
  lineage: lineageApi,
  search: searchApi,
}

export default api

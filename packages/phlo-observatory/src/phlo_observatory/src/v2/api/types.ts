export type V2HealthState = 'ok' | 'warning' | 'error' | 'unknown'

export type V2ServiceStatus =
  | 'running'
  | 'stopped'
  | 'unhealthy'
  | 'starting'
  | 'unknown'

export interface V2Health {
  state: V2HealthState
  message?: string | null
}

export interface V2ExternalLink {
  label: string
  url: string
  kind: string
}

export interface V2CapabilityPage {
  id: string
  label: string
  path: string
  available: boolean
  nav: boolean
  reason?: string | null
  providers: Array<string>
  metadata: Record<string, unknown>
}

export interface V2Capabilities {
  version: number
  pages: Array<V2CapabilityPage>
  features: Record<string, boolean>
  providers: Record<string, Array<string>>
}

export interface V2ResourceRef {
  kind: string
  id: string
  label: string
}

export interface V2Action {
  id: string
  label: string
  kind: string
  enabled: boolean
  requires_confirmation: boolean
  reason?: string | null
}

export interface V2ActionResult {
  action: V2Action
  status: 'succeeded' | 'failed' | 'skipped'
  message: string
  operation?: V2Operation | null
}

export interface V2ServicePort {
  name: string
  target: string
  published?: string | null
}

export interface V2ServiceConfigEntry {
  name: string
  value?: string | null
  description?: string | null
  secret: boolean
}

export interface V2Service {
  id: string
  name: string
  kind: string
  status: V2ServiceStatus
  health: V2Health
  definition_state?: 'configured' | 'available'
  runtime_state?: V2ServiceStatus
  in_stack?: boolean
  disabled?: boolean
  profile?: string | null
  backend?: string
  depends_on: Array<string>
  impacts: Array<string>
  links: Array<V2ExternalLink>
  metadata: Record<string, unknown>
}

export interface V2ServiceDetail {
  service: V2Service
  dependencies: Array<V2Service>
  dependents: Array<V2Service>
  actions: Array<V2Action>
  logs: Array<V2LogEvent>
  ports: Array<V2ServicePort>
  config: Array<V2ServiceConfigEntry>
}

export interface V2Overview {
  health: V2Health
  counters: Record<string, number>
  recent: Array<V2ResourceRef>
}

export interface V2ResourceItem {
  id: string
  name: string
  kind: string
  health?: V2Health | null
  status?: string | null
  summary?: string | null
  updated_at?: string | null
  links?: Array<V2ExternalLink>
  metadata: Record<string, unknown>
}

export interface V2ResourceCollection {
  items: Array<V2ResourceItem>
}

export interface V2Operation {
  id: string
  name: string
  kind: string
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'unknown'
  health: V2Health
  target?: V2ResourceRef | null
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  metadata: Record<string, unknown>
}

export interface V2OperationDetail {
  operation: V2Operation
  related: Array<V2ResourceRef>
  logs: Array<V2LogEvent>
  actions: Array<V2Action>
}

export interface V2Asset {
  id: string
  name: string
  group?: string | null
  description?: string | null
  kinds: Array<string>
  dependencies: Array<string>
  resources: Array<string>
  checks: Array<string>
  metadata: Record<string, unknown>
}

export interface V2AssetDetail {
  asset: V2Asset
  upstream: Array<V2Asset>
  downstream: Array<V2Asset>
  tables: Array<V2Table>
  quality: Array<V2QualityCheck>
  logs: Array<V2LogEvent>
  operations: Array<V2Operation>
  lineage: Array<V2ResourceRef>
  materializations: Array<V2Operation>
  column_lineage: Record<string, Array<string>>
}

export interface V2Table {
  id: string
  name: string
  namespace?: string | null
  asset_id?: string | null
  format?: string | null
  branch?: string | null
  schema_name?: string | null
  metadata: Record<string, unknown>
}

export interface V2TablePreview {
  table: V2Table
  columns: Array<string>
  column_types: Array<string>
  rows: Array<Record<string, unknown>>
  row_count?: number | null
  limit: number
  offset: number
  has_more: boolean
}

export interface V2QueryResult {
  columns: Array<string>
  rows: Array<Record<string, unknown>>
  row_count?: number | null
  effective_sql: string
  limit: number
  offset: number
  warnings: Array<string>
}

export interface V2SavedQuery {
  id: string
  name: string
  sql: string
  branch?: string | null
  created_at: string
  updated_at: string
  metadata: Record<string, unknown>
}

export interface V2StageDiff {
  source: V2Table
  target: V2Table
  columns: Record<string, Array<string>>
  rows: Array<Record<string, unknown>>
  summary: Record<string, number>
  metadata: Record<string, unknown>
}

export interface V2RowJourney {
  table: V2Table
  row_id: string
  row: Record<string, unknown>
  upstream: Array<V2ResourceRef>
  downstream: Array<V2ResourceRef>
  stages: Array<V2ResourceRef>
  logs: Array<V2LogEvent>
  diff: Record<string, unknown>
}

export interface V2QualityCheck {
  id: string
  name: string
  asset_id: string
  status: 'passing' | 'failing' | 'warning' | 'unknown'
  severity?: string | null
  blocking: boolean
  description?: string | null
  metadata: Record<string, unknown>
}

export interface V2QualityDetail {
  check: V2QualityCheck
  asset?: V2Asset | null
  history: Array<V2Operation>
  logs: Array<V2LogEvent>
  actions: Array<V2Action>
}

export interface V2LogEvent {
  id: string
  timestamp?: string | null
  level: string
  message: string
  source?: string | null
  resource?: V2ResourceRef | null
  metadata: Record<string, unknown>
}

export interface V2LogFacets {
  sources: Array<string>
  levels: Array<string>
  resources: Array<V2ResourceRef>
}

export interface V2Branch {
  id: string
  name: string
  current: boolean
  protected: boolean
  metadata: Record<string, unknown>
}

export interface V2BranchDetail {
  branch: V2Branch
  contents: Array<V2ResourceRef>
  commits: Array<V2Operation>
  compare: Record<string, number>
  tables: Array<V2Table>
}

export interface V2Extension {
  id: string
  name: string
  version?: string | null
  enabled: boolean
  routes: Array<string>
  nav: Array<string>
  settings_scope?: string | null
  metadata: Record<string, unknown>
}

export interface V2ExtensionDetail {
  extension: V2Extension
  routes: Array<string>
  nav: Array<string>
  capabilities: Array<V2ResourceRef>
}

export interface V2Setting {
  id: string
  label: string
  value: string | boolean | number | null
  kind: string
  description?: string | null
  metadata: Record<string, unknown>
}

export interface V2Settings {
  items: Array<V2Setting>
}

export interface V2ApiSettings {
  version: number
  defaults: Record<string, string>
  features: Record<string, boolean>
  storage: Record<string, string>
  metadata: Record<string, unknown>
}

export interface V2SearchResult {
  id: string
  label: string
  kind: string
  summary?: string | null
  href?: string | null
  metadata: Record<string, unknown>
}

export interface V2ResourceResult<T> {
  data: T | null
  error: string | null
}

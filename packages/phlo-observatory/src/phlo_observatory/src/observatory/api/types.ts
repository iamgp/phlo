export type ObservatoryHealthState = 'ok' | 'warning' | 'error' | 'unknown'

export type ObservatoryMetadata = Record<string, NonNullable<unknown>>
type ObservatoryRecord = Record<string, NonNullable<unknown>>

export type ObservatoryServiceStatus =
  'running' | 'stopped' | 'unhealthy' | 'starting' | 'unknown'

interface ObservatoryHealth {
  state: ObservatoryHealthState
  message?: string | null
}

interface ObservatoryExternalLink {
  label: string
  url: string
  kind: string
}

export interface ObservatoryCapabilityPage {
  id: string
  label: string
  path: string
  available: boolean
  nav: boolean
  reason?: string | null
  providers: Array<string>
  metadata: ObservatoryMetadata
}

export interface ObservatoryCapabilities {
  version: number
  pages: Array<ObservatoryCapabilityPage>
  features: Record<string, boolean>
  providers: Record<string, Array<string>>
}

export interface ObservatoryWorkflowWizardField {
  name: string
  label: string
  field_type: 'text' | 'textarea' | 'select' | 'checkbox' | 'fields'
  required: boolean
  description?: string | null
  default?: string | number | boolean
  options: Array<string>
  secret: boolean
}

export interface ObservatoryWorkflowWizardContribution {
  id: string
  package: string
  stage: 'source' | 'transform' | 'quality' | 'publish'
  label: string
  description: string
  required_capabilities: Array<string>
  optional_capabilities: Array<string>
  fields: Array<ObservatoryWorkflowWizardField>
  modes: Array<'proposal' | 'apply'>
  metadata: ObservatoryMetadata
}

export interface ObservatoryWorkflowWizardPayload {
  version: number
  stages: Array<'source' | 'transform' | 'quality' | 'publish'>
  contributions: Array<ObservatoryWorkflowWizardContribution>
}

interface ObservatoryWorkflowGraphNode {
  id: string
  contribution_id: string
  stage: 'source' | 'transform' | 'quality' | 'publish'
  values: Record<string, unknown>
}

interface ObservatoryWorkflowGraphEdge {
  id: string
  source: string
  target: string
}

export interface ObservatoryWorkflowGraph {
  nodes: Array<ObservatoryWorkflowGraphNode>
  edges: Array<ObservatoryWorkflowGraphEdge>
}

export interface ObservatoryWorkflowProposalRequest {
  workflow_name: string
  domain: string
  graph: ObservatoryWorkflowGraph
}

interface ObservatoryWorkflowFilePreview {
  path: string
  content: string
  mode: 'create' | 'modify'
}

export interface ObservatoryWorkflowApplyAction {
  id: string
  label: string
  target_files: Array<string>
  conflict_policy: 'preview' | 'skip-if-exists' | 'fail-on-conflict'
  enabled: boolean
  reason?: string | null
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  required_permission?: string | null
  expected_evidence: Array<string>
}

export interface ObservatoryWorkflowProposal {
  workflow_name: string
  domain: string
  selected_contributions: Array<string>
  planned_assets: Array<string>
  planned_tables: Array<string>
  planned_models: Array<string>
  files: Array<ObservatoryWorkflowFilePreview>
  warnings: Array<string>
  missing_capabilities: Array<string>
  disabled_stages: Record<string, string>
  actions: Array<ObservatoryWorkflowApplyAction>
}

export interface ObservatoryWorkflowActionResult {
  action_id: string
  status: 'succeeded' | 'failed' | 'skipped'
  message: string
  files: Array<string>
}

interface ObservatoryResourceRef {
  kind: string
  id: string
  label: string
}

export interface ObservatoryDataProduct {
  id: string
  name: string
  description?: string | null
  owner?: string | null
  classifications: Array<string>
  publication_state: 'draft' | 'published' | 'retired'
  readiness_state: ObservatoryHealthState
  kinds: Array<string>
  source_refs: Array<ObservatoryResourceRef>
  metadata: ObservatoryMetadata
}

export interface ObservatoryDataProductProfile {
  product: ObservatoryDataProduct
  asset?: ObservatoryAsset | null
  tables: Array<ObservatoryTable>
  quality: Array<ObservatoryQualityCheck>
  upstream: Array<ObservatoryResourceRef>
  downstream: Array<ObservatoryResourceRef>
  logs: Array<ObservatoryLogEvent>
  operations: Array<ObservatoryOperation>
  sections: Record<string, boolean>
}

export interface ObservatoryAction {
  id: string
  label: string
  kind: string
  enabled: boolean
  requires_confirmation: boolean
  reason?: string | null
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  required_capability?: string | null
  required_service?: string | null
  required_permission?: string | null
  equivalent_cli_command?: string | null
  expected_evidence: Array<string>
  background_operation_id?: string | null
}

export interface ObservatoryActionResult {
  action: ObservatoryAction
  status: 'succeeded' | 'failed' | 'skipped'
  message: string
  operation?: ObservatoryOperation | null
}

interface ObservatoryServicePort {
  name: string
  target: string
  published?: string | null
}

interface ObservatoryServiceConfigEntry {
  name: string
  value?: string | null
  description?: string | null
  secret: boolean
}

export interface ObservatoryService {
  id: string
  name: string
  kind: string
  status: ObservatoryServiceStatus
  health: ObservatoryHealth
  definition_state?: 'configured' | 'available'
  runtime_state?: ObservatoryServiceStatus
  in_stack?: boolean
  disabled?: boolean
  profile?: string | null
  backend?: string
  depends_on: Array<string>
  impacts: Array<string>
  links: Array<ObservatoryExternalLink>
  metadata: ObservatoryMetadata
}

export interface ObservatoryServiceDetail {
  service: ObservatoryService
  dependencies: Array<ObservatoryService>
  dependents: Array<ObservatoryService>
  actions: Array<ObservatoryAction>
  logs: Array<ObservatoryLogEvent>
  ports: Array<ObservatoryServicePort>
  config: Array<ObservatoryServiceConfigEntry>
}

export interface ObservatoryPackageInstallResult {
  package_name: string
  package_spec: string
  status: 'succeeded' | 'failed' | 'skipped'
  message: string
  services: Array<string>
}

export interface ObservatoryOverview {
  health: ObservatoryHealth
  counters: Record<string, number>
  recent: Array<ObservatoryResourceRef>
}

export interface ObservatoryResourceItem {
  id: string
  name: string
  kind: string
  health?: ObservatoryHealth | null
  status?: string | null
  summary?: string | null
  updated_at?: string | null
  links?: Array<ObservatoryExternalLink>
  metadata: ObservatoryMetadata
}

export interface ObservatorySurfaceItem {
  id: string
  name: string
  kind: string
  health: ObservatoryHealth
  summary?: string | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryOperation {
  id: string
  name: string
  kind: string
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'skipped' | 'unknown'
  health: ObservatoryHealth
  target?: ObservatoryResourceRef | null
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryOperationDetail {
  operation: ObservatoryOperation
  related: Array<ObservatoryResourceRef>
  logs: Array<ObservatoryLogEvent>
  actions: Array<ObservatoryAction>
}

type ObservatoryRunStatus =
  'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'unknown'

export interface ObservatoryRun {
  id: string
  name: string
  status: ObservatoryRunStatus
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  assets: Array<ObservatoryResourceRef>
  checks: Array<ObservatoryResourceRef>
  logs: Array<ObservatoryResourceRef>
  metadata: ObservatoryMetadata
}

export interface ObservatoryAsset {
  id: string
  name: string
  group?: string | null
  description?: string | null
  kinds: Array<string>
  dependencies: Array<string>
  resources: Array<string>
  checks: Array<string>
  metadata: ObservatoryMetadata
}

export interface ObservatoryAssetDetail {
  asset: ObservatoryAsset
  upstream: Array<ObservatoryAsset>
  downstream: Array<ObservatoryAsset>
  tables: Array<ObservatoryTable>
  quality: Array<ObservatoryQualityCheck>
  logs: Array<ObservatoryLogEvent>
  operations: Array<ObservatoryOperation>
  lineage: Array<ObservatoryResourceRef>
  materializations: Array<ObservatoryOperation>
  column_lineage: Record<string, Array<string>>
}

export interface ObservatoryTable {
  id: string
  name: string
  namespace?: string | null
  asset_id?: string | null
  format?: string | null
  branch?: string | null
  schema_name?: string | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryTablePreview {
  table: ObservatoryTable
  columns: Array<string>
  column_types: Array<string>
  rows: Array<ObservatoryRecord>
  row_count?: number | null
  limit: number
  offset: number
  has_more: boolean
}

export interface ObservatoryQueryResult {
  columns: Array<string>
  rows: Array<ObservatoryRecord>
  row_count?: number | null
  effective_sql: string
  limit: number
  offset: number
  warnings: Array<string>
}

export interface ObservatorySavedQuery {
  id: string
  name: string
  sql: string
  branch?: string | null
  created_at: string
  updated_at: string
  metadata: ObservatoryMetadata
}

export interface ObservatoryRowJourney {
  table: ObservatoryTable
  row_id: string
  row: ObservatoryRecord
  upstream: Array<ObservatoryResourceRef>
  downstream: Array<ObservatoryResourceRef>
  stages: Array<ObservatoryResourceRef>
  logs: Array<ObservatoryLogEvent>
  diff: ObservatoryRecord
}

export interface ObservatoryQualityCheck {
  id: string
  name: string
  asset_id: string
  status: 'passing' | 'failing' | 'warning' | 'unknown'
  severity?: string | null
  blocking: boolean
  description?: string | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryQualityDetail {
  check: ObservatoryQualityCheck
  asset?: ObservatoryAsset | null
  history: Array<ObservatoryOperation>
  logs: Array<ObservatoryLogEvent>
  actions: Array<ObservatoryAction>
}

export interface ObservatoryLogEvent {
  id: string
  timestamp?: string | null
  level: string
  message: string
  source?: string | null
  resource?: ObservatoryResourceRef | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryLogFacets {
  sources: Array<string>
  levels: Array<string>
  resources: Array<ObservatoryResourceRef>
}

export interface ObservatoryBranch {
  id: string
  name: string
  current: boolean
  protected: boolean
  metadata: ObservatoryMetadata
}

export interface ObservatoryBranchDetail {
  branch: ObservatoryBranch
  contents: Array<ObservatoryResourceRef>
  commits: Array<ObservatoryOperation>
  compare: Record<string, number>
  tables: Array<ObservatoryTable>
}

export interface ObservatoryExtension {
  id: string
  name: string
  version?: string | null
  enabled: boolean
  routes: Array<string>
  nav: Array<string>
  settings_scope?: string | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryExtensionDetail {
  extension: ObservatoryExtension
  routes: Array<string>
  nav: Array<string>
  capabilities: Array<ObservatoryResourceRef>
}

export interface ObservatorySearchResult {
  id: string
  label: string
  kind: string
  summary?: string | null
  href?: string | null
  metadata: ObservatoryMetadata
}

export interface ObservatoryResourceResult<T> {
  data: T | null
  error: string | null
}

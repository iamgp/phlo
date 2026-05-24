import { createServerFn } from '@tanstack/react-start'

import type {
  V2ActionResult,
  V2Asset,
  V2AssetDetail,
  V2Branch,
  V2BranchDetail,
  V2Capabilities,
  V2Extension,
  V2ExtensionDetail,
  V2LogEvent,
  V2LogFacets,
  V2Metadata,
  V2Operation,
  V2OperationDetail,
  V2Overview,
  V2PackageInstallResult,
  V2QualityCheck,
  V2QualityDetail,
  V2QueryResult,
  V2ResourceItem,
  V2ResourceResult,
  V2RowJourney,
  V2Run,
  V2SavedQuery,
  V2SearchResult,
  V2Service,
  V2ServiceDetail,
  V2SurfaceItem,
  V2Table,
  V2TablePreview,
  V2WorkflowActionResult,
  V2WorkflowProposal,
  V2WorkflowProposalRequest,
  V2WorkflowWizardPayload,
} from './types'
import { apiGet, apiPost } from '@/server/phlo-api'

const V2_API_PREFIX = '/api/observatory/v2'

declare global {
  interface Window {
    __PHLO_API_BROWSER_URL__?: string
  }
}

function apiUnavailable<T>(error: unknown): V2ResourceResult<T> {
  return {
    data: null,
    error:
      error instanceof Error ? error.message : 'Lakehouse API is unavailable',
  }
}

function browserApiBase(): string | null {
  if (typeof window === 'undefined') return null
  const configured =
    window.__PHLO_API_BROWSER_URL__ ??
    document.querySelector<HTMLMetaElement>('meta[name="phlo-api-browser-url"]')
      ?.content
  if (configured !== undefined) return configured
  return null
}

async function browserApiGet<T>(endpoint: string): Promise<T> {
  const base = browserApiBase()
  if (base === null) {
    throw new Error('Browser API fallback is unavailable during SSR')
  }
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 8000)
  let response: Response
  try {
    response = await fetch(`${base}${endpoint}`, {
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('phlo-api request timed out')
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
  if (!response.ok) {
    throw new Error(`phlo-api error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

async function browserApiPost<T>(
  endpoint: string,
  body: Record<string, unknown>,
  timeoutMs = 12000,
): Promise<T> {
  const base = browserApiBase()
  if (base === null) {
    throw new Error('Browser API fallback is unavailable during SSR')
  }
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)
  let response: Response
  try {
    response = await fetch(`${base}${endpoint}`, {
      body: JSON.stringify(body),
      headers: { 'content-type': 'application/json' },
      method: 'POST',
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('phlo-api request timed out')
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? String(payload.detail)
        : `${response.status} ${response.statusText}`
    throw new Error(`phlo-api error: ${detail}`)
  }
  return response.json()
}

async function v2ApiGet<T>(endpoint: string): Promise<T> {
  if (browserApiBase() !== null) return browserApiGet<T>(endpoint)
  return apiGet<T>(endpoint, undefined, 8000)
}

export async function getV2Overview(): Promise<V2ResourceResult<V2Overview>> {
  try {
    const data = await v2ApiGet<V2Overview>(`${V2_API_PREFIX}/overview`)
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2Overview>(error)
  }
}

export async function getV2Capabilities(): Promise<
  V2ResourceResult<V2Capabilities>
> {
  try {
    const data = await v2ApiGet<V2Capabilities>(
      `${V2_API_PREFIX}/surface-capabilities`,
    )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2Capabilities>(error)
  }
}

export async function getV2Services(): Promise<
  V2ResourceResult<Array<V2Service>>
> {
  try {
    const response = await v2ApiGet<{ items: Array<V2Service> }>(
      `${V2_API_PREFIX}/services`,
    )
    return { data: response.items, error: null }
  } catch (error) {
    return apiUnavailable<Array<V2Service>>(error)
  }
}

export async function getV2ServicesDirect(): Promise<
  V2ResourceResult<Array<V2Service>>
> {
  try {
    const response = await browserApiGet<{ items: Array<V2Service> }>(
      `${V2_API_PREFIX}/services`,
    )
    return { data: response.items, error: null }
  } catch (error) {
    return apiUnavailable<Array<V2Service>>(error)
  }
}

export const getV2ServiceDetail = createServerFn()
  .inputValidator((input: { serviceId: string }) => input)
  .handler(
    async ({
      data: { serviceId },
    }): Promise<V2ResourceResult<V2ServiceDetail>> => {
      try {
        const data = await apiGet<V2ServiceDetail>(
          `${V2_API_PREFIX}/services/${encodeURIComponent(serviceId)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2ServiceDetail>(error)
      }
    },
  )

export async function getV2ServiceDetailDirect({
  serviceId,
}: {
  serviceId: string
}): Promise<V2ResourceResult<V2ServiceDetail>> {
  try {
    const data = await browserApiGet<V2ServiceDetail>(
      `${V2_API_PREFIX}/services/${encodeURIComponent(serviceId)}`,
    )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2ServiceDetail>(error)
  }
}

async function getRawCollection<T>(
  endpoint: string,
): Promise<V2ResourceResult<Array<T>>> {
  try {
    const response = await v2ApiGet<{ items: Array<T> }>(
      `${V2_API_PREFIX}/${endpoint}`,
    )
    return { data: response.items, error: null }
  } catch (error) {
    return apiUnavailable<Array<T>>(error)
  }
}

async function getCollection(
  endpoint: string,
): Promise<V2ResourceResult<Array<V2ResourceItem>>> {
  try {
    const response = await v2ApiGet<{ items: Array<Record<string, unknown>> }>(
      `${V2_API_PREFIX}/${endpoint}`,
    )
    return {
      data: response.items.map((item) => normalizeItem(endpoint, item)),
      error: null,
    }
  } catch (error) {
    return apiUnavailable<Array<V2ResourceItem>>(error)
  }
}

export function getV2OperationRecords() {
  return getRawCollection<V2Operation>('operations')
}

export const getV2OperationDetail = createServerFn()
  .inputValidator((input: { operationId: string }) => input)
  .handler(
    async ({
      data: { operationId },
    }): Promise<V2ResourceResult<V2OperationDetail>> => {
      try {
        const data = await apiGet<V2OperationDetail>(
          `${V2_API_PREFIX}/operations/${encodeURIComponent(operationId)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2OperationDetail>(error)
      }
    },
  )

export function getV2RunRecords() {
  return getRawCollection<V2Run>('runs')
}

export function getV2StorageItems() {
  return getRawCollection<V2SurfaceItem>('storage')
}

export function getV2ObservabilityItems() {
  return getRawCollection<V2SurfaceItem>('observability')
}

export function getV2GovernanceItems() {
  return getRawCollection<V2SurfaceItem>('governance')
}

export function getV2CatalogItems() {
  return getRawCollection<V2SurfaceItem>('catalog')
}

export function getV2ApiItems() {
  return getRawCollection<V2SurfaceItem>('apis')
}

export function getV2BiItems() {
  return getRawCollection<V2SurfaceItem>('bi')
}

export function getV2AssetRecords() {
  return getRawCollection<V2Asset>('assets')
}

export const getV2AssetDetail = createServerFn()
  .inputValidator((input: { assetId: string }) => input)
  .handler(
    async ({ data: { assetId } }): Promise<V2ResourceResult<V2AssetDetail>> => {
      try {
        const data = await apiGet<V2AssetDetail>(
          `${V2_API_PREFIX}/assets/${encodeURIComponent(assetId)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2AssetDetail>(error)
      }
    },
  )

export function getV2TableRecords() {
  return getRawCollection<V2Table>('tables')
}

export async function getV2TablePreview({
  data: { tableId, limit = 50, offset = 0 },
}: {
  data: { tableId: string; limit?: number; offset?: number }
}): Promise<V2ResourceResult<V2TablePreview>> {
  try {
    const endpoint = `${V2_API_PREFIX}/table-preview/${encodeURIComponent(tableId)}`
    if (browserApiBase()) {
      const searchParams = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      })
      const data = await browserApiGet<V2TablePreview>(
        `${endpoint}?${searchParams}`,
      )
      return { data, error: null }
    }
    const data = await apiGet<V2TablePreview>(endpoint, { limit, offset }, 8000)
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2TablePreview>(error)
  }
}

export async function runV2Query({
  data: { sql, branch, limit = 100, offset = 0 },
}: {
  data: { sql: string; branch?: string; limit?: number; offset?: number }
}): Promise<V2ResourceResult<V2QueryResult>> {
  try {
    const data = browserApiBase()
      ? await browserApiPost<V2QueryResult>(`${V2_API_PREFIX}/query`, {
          sql,
          branch,
          limit,
          offset,
        })
      : await apiPost<V2QueryResult>(
          `${V2_API_PREFIX}/query`,
          { sql, branch, limit, offset },
          12000,
        )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2QueryResult>(error)
  }
}

export async function getV2SavedQueries(): Promise<
  V2ResourceResult<Array<V2SavedQuery>>
> {
  try {
    const response = await v2ApiGet<{ items: Array<V2SavedQuery> }>(
      `${V2_API_PREFIX}/saved-queries`,
    )
    return { data: response.items, error: null }
  } catch (error) {
    return apiUnavailable<Array<V2SavedQuery>>(error)
  }
}

export async function saveV2Query({
  data: { name, sql, branch, metadata = {} },
}: {
  data: {
    name: string
    sql: string
    branch?: string
    metadata?: Record<string, unknown>
  }
}): Promise<V2ResourceResult<V2SavedQuery>> {
  try {
    const data = browserApiBase()
      ? await browserApiPost<V2SavedQuery>(`${V2_API_PREFIX}/saved-queries`, {
          name,
          sql,
          branch,
          metadata,
        })
      : await apiPost<V2SavedQuery>(
          `${V2_API_PREFIX}/saved-queries`,
          { name, sql, branch, metadata },
          8000,
        )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2SavedQuery>(error)
  }
}

export const getV2RowJourney = createServerFn()
  .inputValidator((input: { tableId: string; rowId: string }) => input)
  .handler(
    async ({
      data: { tableId, rowId },
    }): Promise<V2ResourceResult<V2RowJourney>> => {
      try {
        const data = await apiGet<V2RowJourney>(
          `${V2_API_PREFIX}/row-journey/${encodeURIComponent(tableId)}/${encodeURIComponent(rowId)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2RowJourney>(error)
      }
    },
  )

export function getV2QualityRecords() {
  return getRawCollection<V2QualityCheck>('quality')
}

export const getV2QualityDetail = createServerFn()
  .inputValidator((input: { checkId: string }) => input)
  .handler(
    async ({
      data: { checkId },
    }): Promise<V2ResourceResult<V2QualityDetail>> => {
      try {
        const data = await apiGet<V2QualityDetail>(
          `${V2_API_PREFIX}/quality/${encodeURIComponent(checkId)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2QualityDetail>(error)
      }
    },
  )

export function getV2LogRecords() {
  return getRawCollection<V2LogEvent>('logs')
}

export async function getV2LogFacets(): Promise<V2ResourceResult<V2LogFacets>> {
  try {
    const data = await v2ApiGet<V2LogFacets>(`${V2_API_PREFIX}/logs/facets`)
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2LogFacets>(error)
  }
}

export function getV2Branches() {
  return getCollection('branches')
}

export function getV2BranchRecords() {
  return getRawCollection<V2Branch>('branches')
}

export const getV2BranchDetail = createServerFn()
  .inputValidator((input: { branchName: string }) => input)
  .handler(
    async ({
      data: { branchName },
    }): Promise<V2ResourceResult<V2BranchDetail>> => {
      try {
        const data = await apiGet<V2BranchDetail>(
          `${V2_API_PREFIX}/branches/${encodeURIComponent(branchName)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2BranchDetail>(error)
      }
    },
  )

export function getV2Extensions() {
  return getRawCollection<V2Extension>('extensions')
}

export const getV2ExtensionDetail = createServerFn()
  .inputValidator((input: { extensionId: string }) => input)
  .handler(
    async ({
      data: { extensionId },
    }): Promise<V2ResourceResult<V2ExtensionDetail>> => {
      try {
        const data = await apiGet<V2ExtensionDetail>(
          `${V2_API_PREFIX}/extensions/${encodeURIComponent(extensionId)}`,
          undefined,
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2ExtensionDetail>(error)
      }
    },
  )

export const searchV2 = createServerFn()
  .inputValidator((input: { query: string }) => input)
  .handler(
    async ({
      data: { query },
    }): Promise<V2ResourceResult<Array<V2SearchResult>>> => {
      try {
        const response = await apiGet<{ items: Array<V2SearchResult> }>(
          `${V2_API_PREFIX}/search`,
          { q: query },
          8000,
        )
        return { data: response.items, error: null }
      } catch (error) {
        return apiUnavailable<Array<V2SearchResult>>(error)
      }
    },
  )

export const runV2Action = createServerFn()
  .inputValidator((input: { actionId: string }) => input)
  .handler(
    async ({
      data: { actionId },
    }): Promise<V2ResourceResult<V2ActionResult>> => {
      try {
        const data = await apiPost<V2ActionResult>(
          `${V2_API_PREFIX}/actions`,
          { action_id: actionId },
          130000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2ActionResult>(error)
      }
    },
  )

export async function runV2ActionDirect({
  actionId,
}: {
  actionId: string
}): Promise<V2ResourceResult<V2ActionResult>> {
  try {
    const data = await browserApiPost<V2ActionResult>(
      `${V2_API_PREFIX}/actions`,
      { action_id: actionId },
      130000,
    )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2ActionResult>(error)
  }
}

export const installV2Package = createServerFn()
  .inputValidator((input: { packageName: string }) => input)
  .handler(
    async ({
      data: { packageName },
    }): Promise<V2ResourceResult<V2PackageInstallResult>> => {
      try {
        const data = await apiPost<V2PackageInstallResult>(
          `${V2_API_PREFIX}/packages/install`,
          { package_name: packageName },
          310000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2PackageInstallResult>(error)
      }
    },
  )

export async function installV2PackageDirect({
  packageName,
}: {
  packageName: string
}): Promise<V2ResourceResult<V2PackageInstallResult>> {
  try {
    const data = await browserApiPost<V2PackageInstallResult>(
      `${V2_API_PREFIX}/packages/install`,
      { package_name: packageName },
      310000,
    )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2PackageInstallResult>(error)
  }
}

export const runV2BranchAction = createServerFn()
  .inputValidator((input: { actionId: string }) => input)
  .handler(
    async ({
      data: { actionId },
    }): Promise<V2ResourceResult<V2ActionResult>> => {
      try {
        const data = await apiPost<V2ActionResult>(
          `${V2_API_PREFIX}/branches/actions`,
          { action_id: actionId },
          12000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2ActionResult>(error)
      }
    },
  )

export async function getV2WorkflowWizard(): Promise<
  V2ResourceResult<V2WorkflowWizardPayload>
> {
  try {
    const data = await v2ApiGet<V2WorkflowWizardPayload>(
      `${V2_API_PREFIX}/workflow-wizard`,
    )
    return { data, error: null }
  } catch (error) {
    return apiUnavailable<V2WorkflowWizardPayload>(error)
  }
}

export const createV2WorkflowProposal = createServerFn()
  .inputValidator((input: V2WorkflowProposalRequest) => input)
  .handler(async ({ data }): Promise<V2ResourceResult<V2WorkflowProposal>> => {
    try {
      const proposal = await apiPost<V2WorkflowProposal>(
        `${V2_API_PREFIX}/workflow-wizard/proposals`,
        data,
        12000,
      )
      return { data: proposal, error: null }
    } catch (error) {
      return apiUnavailable<V2WorkflowProposal>(error)
    }
  })

export const runV2WorkflowAction = createServerFn()
  .inputValidator(
    (input: { actionId: string; proposal: V2WorkflowProposal }) => input,
  )
  .handler(
    async ({
      data: { actionId, proposal },
    }): Promise<V2ResourceResult<V2WorkflowActionResult>> => {
      try {
        const result = await apiPost<V2WorkflowActionResult>(
          `${V2_API_PREFIX}/workflow-wizard/actions`,
          { action_id: actionId, proposal },
          12000,
        )
        return { data: result, error: null }
      } catch (error) {
        return apiUnavailable<V2WorkflowActionResult>(error)
      }
    },
  )

function normalizeItem(
  endpoint: string,
  item: V2ResourceItem | Record<string, unknown>,
): V2ResourceItem {
  if ('kind' in item && typeof item.kind === 'string') {
    return item as V2ResourceItem
  }
  const record = item as Record<string, unknown>

  const id = readString(record, 'id') || readString(record, 'name') || endpoint
  const name = readString(record, 'name') || id
  const health = readHealth(record)
  const status = readString(record, 'status') || readBooleanStatus(record)
  const kind = endpointKind(endpoint, record)

  return {
    id,
    name,
    kind,
    health,
    status,
    summary: summaryFor(endpoint, record),
    updated_at:
      readString(record, 'updated_at') || readString(record, 'timestamp'),
    links: [],
    metadata: readRecord(record, 'metadata'),
  }
}

function summaryFor(endpoint: string, item: Record<string, unknown>): string {
  if (endpoint === 'assets') {
    const group = readString(item, 'group')
    const kinds = readStringList(item, 'kinds')
    return [group, kinds.join(', ')].filter(Boolean).join(' · ') || 'Asset'
  }
  if (endpoint === 'tables') {
    return (
      [readString(item, 'namespace'), readString(item, 'format')]
        .filter(Boolean)
        .join(' · ') || 'Table'
    )
  }
  if (endpoint === 'quality') {
    return (
      [readString(item, 'asset_id'), readString(item, 'severity')]
        .filter(Boolean)
        .join(' · ') || 'Quality check'
    )
  }
  if (endpoint === 'logs') {
    return (
      [readString(item, 'level'), readString(item, 'source')]
        .filter(Boolean)
        .join(' · ') || 'Log event'
    )
  }
  if (endpoint === 'branches') {
    return readBoolean(item, 'current') ? 'Current branch' : 'Branch'
  }
  if (endpoint === 'extensions') {
    return (
      [readString(item, 'version'), readString(item, 'settings_scope')]
        .filter(Boolean)
        .join(' · ') || 'Extension'
    )
  }
  if (endpoint === 'operations') {
    return (
      [readString(item, 'kind'), readString(item, 'completed_at')]
        .filter(Boolean)
        .join(' · ') || 'Operation'
    )
  }
  return readString(item, 'summary') || endpoint
}

function endpointKind(endpoint: string, item: Record<string, unknown>): string {
  if (endpoint === 'quality') return 'quality'
  if (endpoint === 'logs') return 'log'
  if (endpoint === 'tables') return 'table'
  if (endpoint === 'branches') return 'branch'
  if (endpoint === 'extensions') return 'extension'
  return readString(item, 'kind') || endpoint.replace(/s$/, '')
}

function readHealth(item: Record<string, unknown>): V2ResourceItem['health'] {
  const health = item.health
  if (!isRecord(health)) return null
  const state = readString(health, 'state')
  if (
    state !== 'ok' &&
    state !== 'warning' &&
    state !== 'error' &&
    state !== 'unknown'
  ) {
    return null
  }
  return { state, message: readString(health, 'message') || null }
}

function readBooleanStatus(item: Record<string, unknown>): string | null {
  if (readBoolean(item, 'current')) return 'current'
  if (readBoolean(item, 'enabled')) return 'enabled'
  if (readBoolean(item, 'protected')) return 'protected'
  return null
}

function readString(item: Record<string, unknown>, key: string): string {
  const value = item[key]
  return typeof value === 'string' ? value : ''
}

function readBoolean(item: Record<string, unknown>, key: string): boolean {
  return item[key] === true
}

function readStringList(
  item: Record<string, unknown>,
  key: string,
): Array<string> {
  const value = item[key]
  return Array.isArray(value)
    ? value.filter((entry): entry is string => typeof entry === 'string')
    : []
}

function readRecord(item: Record<string, unknown>, key: string): V2Metadata {
  const value = item[key]
  return isRecord(value) ? (value as V2Metadata) : {}
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

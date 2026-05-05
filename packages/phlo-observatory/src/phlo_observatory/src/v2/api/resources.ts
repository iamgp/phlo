import { createServerFn } from '@tanstack/react-start'

import type {
  V2ActionResult,
  V2ApiSettings,
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
  V2Settings,
  V2StageDiff,
  V2SurfaceItem,
  V2Table,
  V2TablePreview,
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
  return window.__PHLO_API_BROWSER_URL__ || null
}

async function browserApiGet<T>(endpoint: string): Promise<T> {
  const base = browserApiBase()
  if (!base) throw new Error('Browser API fallback is unavailable during SSR')
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

export const getV2Overview = createServerFn().handler(
  async (): Promise<V2ResourceResult<V2Overview>> => {
    try {
      const data = await apiGet<V2Overview>(
        `${V2_API_PREFIX}/overview`,
        undefined,
        8000,
      )
      return { data, error: null }
    } catch (error) {
      return apiUnavailable<V2Overview>(error)
    }
  },
)

export const getV2Capabilities = createServerFn().handler(
  async (): Promise<V2ResourceResult<V2Capabilities>> => {
    try {
      const data = await apiGet<V2Capabilities>(
        `${V2_API_PREFIX}/capabilities`,
        undefined,
        8000,
      )
      return { data, error: null }
    } catch (error) {
      return apiUnavailable<V2Capabilities>(error)
    }
  },
)

export const getV2Services = createServerFn().handler(
  async (): Promise<V2ResourceResult<Array<V2Service>>> => {
    try {
      const response = await apiGet<{ items: Array<V2Service> }>(
        `${V2_API_PREFIX}/services`,
        undefined,
        8000,
      )
      return { data: response.items, error: null }
    } catch (error) {
      return apiUnavailable<Array<V2Service>>(error)
    }
  },
)

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

async function getRawCollection<T>(
  endpoint: string,
): Promise<V2ResourceResult<Array<T>>> {
  try {
    const response = await apiGet<{ items: Array<T> }>(
      `${V2_API_PREFIX}/${endpoint}`,
      undefined,
      8000,
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
    const response = await apiGet<{ items: Array<Record<string, unknown>> }>(
      `${V2_API_PREFIX}/${endpoint}`,
      undefined,
      8000,
    )
    return {
      data: response.items.map((item) => normalizeItem(endpoint, item)),
      error: null,
    }
  } catch (error) {
    return apiUnavailable<Array<V2ResourceItem>>(error)
  }
}

export const getV2Operations = createServerFn().handler(() =>
  getCollection('operations'),
)

export const getV2OperationRecords = createServerFn().handler(() =>
  getRawCollection<V2Operation>('operations'),
)

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

export const getV2RunRecords = createServerFn().handler(() =>
  getRawCollection<V2Run>('runs'),
)

export const getV2StorageItems = createServerFn().handler(() =>
  getRawCollection<V2SurfaceItem>('storage'),
)

export const getV2ObservabilityItems = createServerFn().handler(() =>
  getRawCollection<V2SurfaceItem>('observability'),
)

export const getV2GovernanceItems = createServerFn().handler(() =>
  getRawCollection<V2SurfaceItem>('governance'),
)

export const getV2CatalogItems = createServerFn().handler(() =>
  getRawCollection<V2SurfaceItem>('catalog'),
)

export const getV2ApiItems = createServerFn().handler(() =>
  getRawCollection<V2SurfaceItem>('apis'),
)

export const getV2BiItems = createServerFn().handler(() =>
  getRawCollection<V2SurfaceItem>('bi'),
)

export const getV2Assets = createServerFn().handler(() =>
  getCollection('assets'),
)

export const getV2AssetRecords = createServerFn().handler(() =>
  getRawCollection<V2Asset>('assets'),
)

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

export const getV2Tables = createServerFn().handler(() =>
  getCollection('tables'),
)

export const getV2TableRecords = createServerFn().handler(() =>
  getRawCollection<V2Table>('tables'),
)

export const getV2TablePreview = createServerFn()
  .inputValidator(
    (input: { tableId: string; limit?: number; offset?: number }) => input,
  )
  .handler(
    async ({
      data: { tableId, limit = 50, offset = 0 },
    }): Promise<V2ResourceResult<V2TablePreview>> => {
      try {
        const data = await apiGet<V2TablePreview>(
          `${V2_API_PREFIX}/table-preview/${encodeURIComponent(tableId)}`,
          { limit, offset },
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2TablePreview>(error)
      }
    },
  )

export const runV2Query = createServerFn()
  .inputValidator(
    (input: {
      sql: string
      branch?: string
      limit?: number
      offset?: number
    }) => input,
  )
  .handler(
    async ({
      data: { sql, branch, limit = 100, offset = 0 },
    }): Promise<V2ResourceResult<V2QueryResult>> => {
      try {
        const data = await apiPost<V2QueryResult>(
          `${V2_API_PREFIX}/query`,
          { sql, branch, limit, offset },
          12000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2QueryResult>(error)
      }
    },
  )

export const getV2SavedQueries = createServerFn().handler(
  async (): Promise<V2ResourceResult<Array<V2SavedQuery>>> => {
    try {
      const response = await apiGet<{ items: Array<V2SavedQuery> }>(
        `${V2_API_PREFIX}/saved-queries`,
        undefined,
        8000,
      )
      return { data: response.items, error: null }
    } catch (error) {
      return apiUnavailable<Array<V2SavedQuery>>(error)
    }
  },
)

export const saveV2Query = createServerFn()
  .inputValidator(
    (input: {
      name: string
      sql: string
      branch?: string
      metadata?: Record<string, unknown>
    }) => input,
  )
  .handler(
    async ({
      data: { name, sql, branch, metadata = {} },
    }): Promise<V2ResourceResult<V2SavedQuery>> => {
      try {
        const data = await apiPost<V2SavedQuery>(
          `${V2_API_PREFIX}/saved-queries`,
          { name, sql, branch, metadata },
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2SavedQuery>(error)
      }
    },
  )

export const getV2StageDiff = createServerFn()
  .inputValidator(
    (input: { sourceTableId: string; targetTableId: string }) => input,
  )
  .handler(
    async ({
      data: { sourceTableId, targetTableId },
    }): Promise<V2ResourceResult<V2StageDiff>> => {
      try {
        const data = await apiGet<V2StageDiff>(
          `${V2_API_PREFIX}/stage-diff`,
          { source_table_id: sourceTableId, target_table_id: targetTableId },
          8000,
        )
        return { data, error: null }
      } catch (error) {
        return apiUnavailable<V2StageDiff>(error)
      }
    },
  )

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

export const getV2Quality = createServerFn().handler(() =>
  getCollection('quality'),
)

export const getV2QualityRecords = createServerFn().handler(() =>
  getRawCollection<V2QualityCheck>('quality'),
)

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

export const getV2Logs = createServerFn().handler(() => getCollection('logs'))

export const getV2LogRecords = createServerFn().handler(() =>
  getRawCollection<V2LogEvent>('logs'),
)

export const getV2LogFacets = createServerFn().handler(
  async (): Promise<V2ResourceResult<V2LogFacets>> => {
    try {
      const data = await apiGet<V2LogFacets>(
        `${V2_API_PREFIX}/logs/facets`,
        undefined,
        8000,
      )
      return { data, error: null }
    } catch (error) {
      return apiUnavailable<V2LogFacets>(error)
    }
  },
)

export const getV2Branches = createServerFn().handler(() =>
  getCollection('branches'),
)

export const getV2BranchRecords = createServerFn().handler(() =>
  getRawCollection<V2Branch>('branches'),
)

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

export const getV2Extensions = createServerFn().handler(() =>
  getRawCollection<V2Extension>('extensions'),
)

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

export const getV2Settings = createServerFn().handler(
  async (): Promise<V2ResourceResult<V2Settings>> => {
    try {
      const data = await apiGet<V2ApiSettings>(
        `${V2_API_PREFIX}/settings`,
        undefined,
        8000,
      )
      return { data: normalizeSettings(data), error: null }
    } catch (error) {
      return apiUnavailable<V2Settings>(error)
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

function normalizeSettings(settings: V2ApiSettings): V2Settings {
  const metadata = Object.entries(settings.metadata).map(([key, value]) => ({
    id: `metadata:${key}`,
    label: labelize(key),
    value: valueToSetting(value),
    kind: 'metadata',
    description: 'Control-plane metadata',
    metadata: {},
  }))
  const defaults = Object.entries(settings.defaults).map(([key, value]) => ({
    id: `default:${key}`,
    label: labelize(key),
    value,
    kind: 'default',
    description: 'Default control-plane value',
    metadata: {},
  }))
  const features = Object.entries(settings.features).map(([key, value]) => ({
    id: `feature:${key}`,
    label: labelize(key),
    value,
    kind: 'feature',
    description: value ? 'Enabled' : 'Disabled',
    metadata: {},
  }))
  const storage = Object.entries(settings.storage).map(([key, value]) => ({
    id: `storage:${key}`,
    label: labelize(key),
    value,
    kind: 'storage',
    description: 'Storage backend',
    metadata: {},
  }))

  return { items: [...metadata, ...defaults, ...features, ...storage] }
}

function valueToSetting(value: unknown): string | boolean | number | null {
  if (value === null || value === undefined) return null
  if (
    typeof value === 'string' ||
    typeof value === 'boolean' ||
    typeof value === 'number'
  ) {
    return value
  }
  return JSON.stringify(value)
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

function labelize(value: string): string {
  return value
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

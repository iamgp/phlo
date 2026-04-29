import { createServerFn } from '@tanstack/react-start'

import type {
  V2ApiSettings,
  V2Asset,
  V2AssetDetail,
  V2BranchDetail,
  V2ExtensionDetail,
  V2LogEvent,
  V2LogFacets,
  V2Operation,
  V2OperationDetail,
  V2Overview,
  V2QualityCheck,
  V2QualityDetail,
  V2ResourceCollection,
  V2ResourceItem,
  V2ResourceResult,
  V2SearchResult,
  V2Service,
  V2ServiceDetail,
  V2Settings,
  V2Table,
  V2TablePreview,
} from './types'
import { apiGet } from '@/server/phlo-api'

const V2_API_PREFIX = '/api/observatory/v2'

function apiUnavailable<T>(error: unknown): V2ResourceResult<T> {
  return {
    data: null,
    error: error instanceof Error ? error.message : 'phlo-api is unavailable',
  }
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
    const response = await apiGet<
      V2ResourceCollection | { items: Array<Record<string, unknown>> }
    >(`${V2_API_PREFIX}/${endpoint}`, undefined, 8000)
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
  getCollection('extensions'),
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

function normalizeItem(
  endpoint: string,
  item: V2ResourceItem | Record<string, unknown>,
): V2ResourceItem {
  if ('kind' in item && typeof item.kind === 'string') {
    return item as V2ResourceItem
  }

  const id = readString(item, 'id') || readString(item, 'name') || endpoint
  const name = readString(item, 'name') || id
  const health = readHealth(item)
  const status = readString(item, 'status') || readBooleanStatus(item)
  const kind = endpointKind(endpoint, item)

  return {
    id,
    name,
    kind,
    health,
    status,
    summary: summaryFor(endpoint, item),
    updated_at: readString(item, 'updated_at') || readString(item, 'timestamp'),
    links: [],
    metadata: readRecord(item, 'metadata'),
  }
}

function normalizeSettings(settings: V2ApiSettings): V2Settings {
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

  return { items: [...defaults, ...features, ...storage] }
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

function readRecord(
  item: Record<string, unknown>,
  key: string,
): Record<string, unknown> {
  const value = item[key]
  return isRecord(value) ? value : {}
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function labelize(value: string): string {
  return value
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

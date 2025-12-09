/**
 * Dagster Server Functions
 *
 * Server-side functions for interacting with the Dagster GraphQL API.
 * These run only on the server and can access environment variables securely.
 */

import { createServerFn } from '@tanstack/react-start'

// Types for health metrics
export interface HealthMetrics {
  assetsTotal: number
  assetsHealthy: number
  failedJobs24h: number
  qualityChecksPassing: number
  qualityChecksTotal: number
  staleAssets: number
  lastUpdated: string
}

export interface DagsterConnectionStatus {
  connected: boolean
  error?: string
  version?: string
}

// GraphQL query to get asset counts and run status
const HEALTH_QUERY = `
  query HealthMetrics {
    assetsOrError {
      ... on AssetConnection {
        nodes {
          key {
            path
          }
          assetMaterializations(limit: 1) {
            timestamp
          }
        }
      }
      ... on PythonError {
        message
      }
    }
    runsOrError(filter: { statuses: [FAILURE], createdBefore: null }, limit: 100) {
      ... on Runs {
        results {
          id
          status
          startTime
          endTime
        }
      }
      ... on PythonError {
        message
      }
    }
  }
`

// Simple version query to check connectivity
const VERSION_QUERY = `
  query Version {
    version
  }
`

/**
 * Check if Dagster is reachable
 */
export const checkDagsterConnection = createServerFn().handler(
  async (): Promise<DagsterConnectionStatus> => {
    const dagsterUrl =
      process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

    try {
      const response = await fetch(dagsterUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: VERSION_QUERY }),
        signal: AbortSignal.timeout(5000), // 5 second timeout
      })

      if (!response.ok) {
        return {
          connected: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      const data = await response.json()

      if (data.errors) {
        return {
          connected: false,
          error: data.errors[0]?.message || 'GraphQL error',
        }
      }

      return {
        connected: true,
        version: data.data?.version,
      }
    } catch (error) {
      return {
        connected: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  },
)

/**
 * Get health metrics from Dagster
 */
export const getHealthMetrics = createServerFn().handler(
  async (): Promise<HealthMetrics | { error: string }> => {
    const dagsterUrl =
      process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

    try {
      const response = await fetch(dagsterUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: HEALTH_QUERY }),
        signal: AbortSignal.timeout(10000), // 10 second timeout
      })

      if (!response.ok) {
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const result = await response.json()

      if (result.errors) {
        return { error: result.errors[0]?.message || 'GraphQL error' }
      }

      const { assetsOrError, runsOrError } = result.data

      // Handle asset data
      let assetsTotal = 0
      let staleAssets = 0
      const now = Date.now()
      const staleThreshold = 24 * 60 * 60 * 1000 // 24 hours

      if (assetsOrError.__typename !== 'PythonError' && assetsOrError.nodes) {
        assetsTotal = assetsOrError.nodes.length

        for (const asset of assetsOrError.nodes) {
          const lastMat = asset.assetMaterializations?.[0]
          if (lastMat) {
            const matTime = Number(lastMat.timestamp)
            if (now - matTime > staleThreshold) {
              staleAssets++
            }
          } else {
            // Never materialized = stale
            staleAssets++
          }
        }
      }

      // Handle run data - count failed runs in last 24 hours
      let failedJobs24h = 0
      const oneDayAgo = now - staleThreshold

      if (runsOrError.__typename !== 'PythonError' && runsOrError.results) {
        for (const run of runsOrError.results) {
          const startTime = run.startTime ? Number(run.startTime) * 1000 : 0
          if (startTime > oneDayAgo) {
            failedJobs24h++
          }
        }
      }

      return {
        assetsTotal,
        assetsHealthy: assetsTotal - staleAssets,
        failedJobs24h,
        qualityChecksPassing: 0, // TODO: Implement quality checks query
        qualityChecksTotal: 0,
        staleAssets,
        lastUpdated: new Date().toISOString(),
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  },
)

// Types for asset list and detail views
export interface Asset {
  id: string
  key: Array<string>
  keyPath: string
  description?: string
  computeKind?: string
  groupName?: string
  lastMaterialization?: {
    timestamp: string
    runId: string
  }
  hasMaterializePermission: boolean
}

// Column lineage dependency - shows where a column comes from
export interface ColumnLineageDep {
  assetKey: Array<string>
  columnName: string
}

export interface AssetDetails extends Asset {
  opNames: Array<string>
  metadata: Array<{
    key: string
    value: string
  }>
  columns?: Array<{
    name: string
    type: string
    description?: string
  }>
  // Column lineage: maps column name -> list of upstream dependencies
  columnLineage?: Record<string, Array<ColumnLineageDep>>
  assetType?: string
  partitionDefinition?: {
    description: string
  }
}

// GraphQL query for asset list
const ASSETS_QUERY = `
  query AssetsQuery {
    assetsOrError {
      ... on AssetConnection {
        nodes {
          id
          key {
            path
          }
          definition {
            description
            computeKind
            groupName
            hasMaterializePermission
            opNames
          }
          assetMaterializations(limit: 1) {
            timestamp
            runId
          }
        }
      }
      ... on PythonError {
        message
      }
    }
  }
`

// GraphQL query for single asset details
const ASSET_DETAILS_QUERY = `
  query AssetDetailsQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        definition {
          description
          computeKind
          groupName
          hasMaterializePermission
          opNames
          metadataEntries {
            label
            description
            ... on TextMetadataEntry {
              text
            }
            ... on TableSchemaMetadataEntry {
              schema {
                columns {
                  name
                  type
                  description
                }
              }
            }
            ... on TableColumnLineageMetadataEntry {
              lineage {
                columnName
                columnDeps {
                  assetKey {
                    path
                  }
                  columnName
                }
              }
            }
          }
          partitionDefinition {
            description
          }
        }
        assetMaterializations(limit: 1) {
          timestamp
          runId
          metadataEntries {
            label
            __typename
            ... on TableSchemaMetadataEntry {
              schema {
                columns {
                  name
                  type
                  description
                }
              }
            }
            ... on TableColumnLineageMetadataEntry {
              lineage {
                columnName
                columnDeps {
                  assetKey {
                    path
                  }
                  columnName
                }
              }
            }
          }
        }
      }
      ... on AssetNotFoundError {
        message
      }
    }
  }
`

/**
 * Get all assets for list view
 */
export const getAssets = createServerFn().handler(
  async (): Promise<Array<Asset> | { error: string }> => {
    const dagsterUrl =
      process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

    try {
      const response = await fetch(dagsterUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: ASSETS_QUERY }),
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const result = await response.json()

      if (result.errors) {
        return { error: result.errors[0]?.message || 'GraphQL error' }
      }

      const { assetsOrError } = result.data

      if (assetsOrError.__typename === 'PythonError') {
        return { error: assetsOrError.message }
      }

      const assets: Array<Asset> = assetsOrError.nodes.map(
        (node: {
          id: string
          key: { path: Array<string> }
          definition?: {
            description?: string
            computeKind?: string
            groupName?: string
            hasMaterializePermission?: boolean
          }
          assetMaterializations?: Array<{
            timestamp: string
            runId: string
          }>
        }) => ({
          id: node.id,
          key: node.key.path,
          keyPath: node.key.path.join('/'),
          description: node.definition?.description,
          computeKind: node.definition?.computeKind,
          groupName: node.definition?.groupName,
          hasMaterializePermission:
            node.definition?.hasMaterializePermission ?? false,
          lastMaterialization: node.assetMaterializations?.[0]
            ? {
                timestamp: node.assetMaterializations[0].timestamp,
                runId: node.assetMaterializations[0].runId,
              }
            : undefined,
        }),
      )

      return assets
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  },
)

/**
 * Get details for a single asset (Server Function)
 * Called with: getAssetDetails({ data: 'assetKeyPath' })
 */
export const getAssetDetails = createServerFn()
  .inputValidator((input: string) => input)
  .handler(
    async ({
      data: assetKeyPath,
    }): Promise<AssetDetails | { error: string }> => {
      if (!assetKeyPath) {
        return { error: 'Asset key is required' }
      }

      const assetKey = assetKeyPath.split('/')
      const dagsterUrl =
        process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

      try {
        const response = await fetch(dagsterUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: ASSET_DETAILS_QUERY,
            variables: { assetKey: { path: assetKey } },
          }),
          signal: AbortSignal.timeout(10000),
        })

        if (!response.ok) {
          return { error: `HTTP ${response.status}: ${response.statusText}` }
        }

        const result = await response.json()

        if (result.errors) {
          return { error: result.errors[0]?.message || 'GraphQL error' }
        }

        const { assetOrError } = result.data

        if (assetOrError.__typename === 'AssetNotFoundError') {
          return { error: assetOrError.message || 'Asset not found' }
        }

        // Type for lineage in metadata entries
        type LineageEntry = {
          columnName: string
          columnDeps: Array<{
            assetKey: { path: Array<string> }
            columnName: string
          }>
        }

        type MetadataEntry = {
          label: string
          description?: string
          text?: string
          __typename?: string
          schema?: {
            columns: Array<{
              name: string
              type: string
              description?: string
            }>
          }
          lineage?: Array<LineageEntry>
        }

        const asset = assetOrError as {
          id: string
          key: { path: Array<string> }
          definition?: {
            description?: string
            computeKind?: string
            groupName?: string
            hasMaterializePermission?: boolean
            opNames?: Array<string>
            metadataEntries?: Array<MetadataEntry>
            partitionDefinition?: { description: string }
          }
          assetMaterializations?: Array<{
            timestamp: string
            runId: string
            metadataEntries?: Array<MetadataEntry>
          }>
        }

        // Extract columns from TableSchemaMetadataEntry
        // Check materialization metadata first (from fetch_column_metadata), then definition
        const matSchemaEntry =
          asset.assetMaterializations?.[0]?.metadataEntries?.find(
            (e) => e.schema || e.__typename === 'TableSchemaMetadataEntry',
          )
        const defSchemaEntry = asset.definition?.metadataEntries?.find(
          (e) => e.schema,
        )
        const columns =
          matSchemaEntry?.schema?.columns ?? defSchemaEntry?.schema?.columns

        // Extract column lineage from TableColumnLineageMetadataEntry
        const matLineageEntry =
          asset.assetMaterializations?.[0]?.metadataEntries?.find(
            (e) =>
              e.lineage || e.__typename === 'TableColumnLineageMetadataEntry',
          )
        const defLineageEntry = asset.definition?.metadataEntries?.find(
          (e) => e.lineage,
        )
        const lineageData = matLineageEntry?.lineage ?? defLineageEntry?.lineage

        // Convert lineage array to Record<columnName, deps[]>
        const columnLineage:
          | Record<string, Array<ColumnLineageDep>>
          | undefined = lineageData
          ? lineageData.reduce(
              (acc, entry) => {
                acc[entry.columnName] = entry.columnDeps.map((dep) => ({
                  assetKey: dep.assetKey.path,
                  columnName: dep.columnName,
                }))
                return acc
              },
              {} as Record<string, Array<ColumnLineageDep>>,
            )
          : undefined

        return {
          id: asset.id,
          key: asset.key.path,
          keyPath: asset.key.path.join('/'),
          description: asset.definition?.description,
          computeKind: asset.definition?.computeKind,
          groupName: asset.definition?.groupName,
          hasMaterializePermission:
            asset.definition?.hasMaterializePermission ?? false,
          opNames: asset.definition?.opNames ?? [],
          metadata: (asset.definition?.metadataEntries ?? [])
            .filter((e) => !e.schema) // Exclude TableSchema from simple metadata
            .map((e) => ({
              key: e.label,
              value: e.text || e.description || '',
            })),
          columns,
          columnLineage,
          partitionDefinition: asset.definition?.partitionDefinition,
          lastMaterialization: asset.assetMaterializations?.[0]
            ? {
                timestamp: asset.assetMaterializations[0].timestamp,
                runId: asset.assetMaterializations[0].runId,
              }
            : undefined,
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

// Types for materialization history
export interface MaterializationEvent {
  timestamp: string
  runId: string
  status: 'SUCCESS' | 'FAILURE' | 'IN_PROGRESS'
  stepKey?: string
  metadata: Array<{
    key: string
    value: string
  }>
  duration?: number
}

// GraphQL query for materialization history
const MATERIALIZATION_HISTORY_QUERY = `
  query MaterializationHistory($assetKey: AssetKeyInput!, $limit: Int!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        assetMaterializations(limit: $limit) {
          timestamp
          runId
          stepKey
          metadataEntries {
            label
            ... on TextMetadataEntry {
              text
            }
            ... on IntMetadataEntry {
              intValue
            }
            ... on FloatMetadataEntry {
              floatValue
            }
          }
        }
      }
      ... on AssetNotFoundError {
        message
      }
    }
  }
`

/**
 * Get materialization history for an asset
 */
export const getMaterializationHistory = createServerFn()
  .inputValidator((input: { assetKey: string; limit?: number }) => input)
  .handler(
    async ({
      data: { assetKey, limit = 20 },
    }): Promise<Array<MaterializationEvent> | { error: string }> => {
      const dagsterUrl =
        process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

      try {
        const response = await fetch(dagsterUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: MATERIALIZATION_HISTORY_QUERY,
            variables: {
              assetKey: { path: assetKey.split('/') },
              limit,
            },
          }),
          signal: AbortSignal.timeout(10000),
        })

        if (!response.ok) {
          return { error: `HTTP ${response.status}: ${response.statusText}` }
        }

        const result = await response.json()

        if (result.errors) {
          return { error: result.errors[0]?.message || 'GraphQL error' }
        }

        const { assetOrError } = result.data

        if (assetOrError.__typename === 'AssetNotFoundError') {
          return { error: assetOrError.message || 'Asset not found' }
        }

        type MetadataEntry = {
          label: string
          text?: string
          intValue?: string
          floatValue?: number
        }

        type MaterializationRaw = {
          timestamp: string
          runId: string
          stepKey?: string
          metadataEntries?: Array<MetadataEntry>
        }

        const materializations = (assetOrError.assetMaterializations || []).map(
          (mat: MaterializationRaw): MaterializationEvent => ({
            timestamp: mat.timestamp,
            runId: mat.runId,
            status: 'SUCCESS', // Materializations are always successful (failures don't create them)
            stepKey: mat.stepKey,
            metadata: (mat.metadataEntries || []).map((e) => ({
              key: e.label,
              value:
                e.text ||
                (e.intValue !== undefined ? String(e.intValue) : '') ||
                (e.floatValue !== undefined ? String(e.floatValue) : '') ||
                '',
            })),
          }),
        )

        return materializations
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

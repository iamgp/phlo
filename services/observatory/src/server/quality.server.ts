/**
 * Quality Server Functions
 *
 * Server-side functions for aggregating quality check results from Dagster.
 * Powers the Quality Center dashboard and asset quality tabs.
 */

import { createServerFn } from '@tanstack/react-start'

// Types for quality data
export interface QualityCheck {
  name: string
  assetKey: Array<string>
  description?: string
  severity: 'ERROR' | 'WARN'
  status: 'PASSED' | 'FAILED' | 'SKIPPED' | 'IN_PROGRESS'
  lastExecutionTime?: string
  lastResult?: {
    passed: boolean
    metadata?: Record<string, string | number | boolean | null | undefined>
  }
}

export interface QualityOverview {
  totalChecks: number
  passingChecks: number
  failingChecks: number
  warningChecks: number
  qualityScore: number // 0-100 percentage
  byCategory: Array<{
    category: string
    passing: number
    total: number
    percentage: number
  }>
  trend: Array<{
    date: string
    score: number
  }>
}

export interface CheckExecution {
  timestamp: string
  passed: boolean
  runId?: string
  metadata?: Record<string, string | number | boolean | null | undefined>
}

// GraphQL query for asset checks - accessed through assetNodes
const ASSET_CHECKS_QUERY = `
  query AssetChecksQuery {
    assetNodes {
      id
      assetKey {
        path
      }
      assetChecksOrError {
        ... on AssetChecks {
          checks {
            name
            description
          }
        }
        ... on AssetCheckNeedsMigrationError {
          message
        }
      }
    }
  }
`

// GraphQL query for check executions for a specific asset
const ASSET_CHECK_EXECUTIONS_QUERY = `
  query AssetCheckExecutionsQuery($assetKey: AssetKeyInput!, $limit: Int!) {
    assetCheckExecutions(assetKey: $assetKey, limit: $limit) {
      id
      status
      runId
      timestamp
      checkName
      evaluation {
        targetMaterialization {
          timestamp
        }
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
          ... on BoolMetadataEntry {
            boolValue
          }
        }
      }
    }
  }
`

// Get Dagster URL from environment
const getDagsterUrl = () =>
  process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

/**
 * Get overview of all quality metrics
 */
export const getQualityOverview = createServerFn().handler(
  async (): Promise<QualityOverview | { error: string }> => {
    const dagsterUrl = getDagsterUrl()

    try {
      const response = await fetch(dagsterUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: ASSET_CHECKS_QUERY }),
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const result = await response.json()

      if (result.errors) {
        return { error: result.errors[0]?.message || 'GraphQL error' }
      }

      const assetNodes = result.data?.assetNodes || []

      // Count total checks across all assets
      let totalChecks = 0
      for (const node of assetNodes) {
        const checksOrError = node.assetChecksOrError
        if (checksOrError?.checks) {
          totalChecks += checksOrError.checks.length
        }
      }

      // For now, return placeholder data - actual pass/fail requires execution queries
      return {
        totalChecks,
        passingChecks: totalChecks, // Assume all passing until we fetch executions
        failingChecks: 0,
        warningChecks: 0,
        qualityScore: totalChecks > 0 ? 100 : 0,
        byCategory:
          totalChecks > 0
            ? [
                {
                  category: 'Completeness',
                  passing: totalChecks,
                  total: totalChecks,
                  percentage: 100,
                },
                {
                  category: 'Freshness',
                  passing: totalChecks,
                  total: totalChecks,
                  percentage: 100,
                },
                {
                  category: 'Accuracy',
                  passing: totalChecks,
                  total: totalChecks,
                  percentage: 100,
                },
              ]
            : [],
        trend: [],
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  },
)

/**
 * Get quality checks for a specific asset
 */
export const getAssetChecks = createServerFn()
  .inputValidator((input: { assetKey: Array<string> }) => input)
  .handler(
    async ({
      data: { assetKey },
    }): Promise<Array<QualityCheck> | { error: string }> => {
      const dagsterUrl = getDagsterUrl()

      try {
        // Fetch check executions for this asset
        const response = await fetch(dagsterUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: ASSET_CHECK_EXECUTIONS_QUERY,
            variables: {
              assetKey: { path: assetKey },
              limit: 50,
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

        const executions = result.data?.assetCheckExecutions || []

        // Group by check name and get latest result
        const checkMap = new Map<string, QualityCheck>()

        for (const execution of executions) {
          const checkName = execution.checkName
          if (!checkMap.has(checkName)) {
            checkMap.set(checkName, {
              name: checkName,
              assetKey,
              severity: 'ERROR',
              status:
                execution.status === 'SUCCEEDED'
                  ? 'PASSED'
                  : execution.status === 'FAILED'
                    ? 'FAILED'
                    : 'SKIPPED',
              lastExecutionTime: execution.timestamp,
              lastResult: {
                passed: execution.status === 'SUCCEEDED',
                metadata: {},
              },
            })
          }
        }

        return Array.from(checkMap.values())
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get execution history for a specific check
 */
export const getCheckHistory = createServerFn()
  .inputValidator(
    (input: { assetKey: Array<string>; checkName: string; limit?: number }) =>
      input,
  )
  .handler(
    async ({
      data: { assetKey, limit = 20 },
    }): Promise<Array<CheckExecution> | { error: string }> => {
      const dagsterUrl = getDagsterUrl()

      try {
        const response = await fetch(dagsterUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: ASSET_CHECK_EXECUTIONS_QUERY,
            variables: {
              assetKey: { path: assetKey },
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

        const executions = result.data?.assetCheckExecutions || []

        return executions.map(
          (exec: {
            timestamp: string
            status: string
            runId?: string
            evaluation?: {
              metadataEntries?: Array<{ label: string; text?: string }>
            }
          }) => ({
            timestamp: exec.timestamp,
            passed: exec.status === 'SUCCEEDED',
            runId: exec.runId,
            metadata: exec.evaluation?.metadataEntries?.reduce(
              (
                acc: Record<
                  string,
                  string | number | boolean | null | undefined
                >,
                entry: { label: string; text?: string },
              ) => {
                acc[entry.label] = entry.text
                return acc
              },
              {},
            ),
          }),
        )
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get all currently failing checks
 */
export const getFailingChecks = createServerFn().handler(
  (): Promise<Array<QualityCheck> | { error: string }> => {
    // TODO: Implement query for failing checks across all assets
    // This would require a different GraphQL query or aggregation

    // For now, return empty array
    return Promise.resolve([])
  },
)

/**
 * Get quality checks with their latest status (for dashboard)
 */
export const getQualityDashboard = createServerFn().handler(
  async (): Promise<
    | {
        overview: QualityOverview
        failingChecks: Array<QualityCheck>
        recentExecutions: Array<CheckExecution>
      }
    | { error: string }
  > => {
    try {
      const [overviewResult, failingResult] = await Promise.all([
        getQualityOverview(),
        getFailingChecks(),
      ])

      if ('error' in overviewResult) {
        return overviewResult
      }

      if ('error' in failingResult) {
        return failingResult
      }

      return {
        overview: overviewResult,
        failingChecks: failingResult,
        recentExecutions: [], // TODO: Fetch recent executions across all assets
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  },
)

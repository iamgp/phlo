/**
 * Quality Server Functions
 *
 * Server-side functions for aggregating quality check results from Dagster.
 * Powers the Quality Center dashboard and asset quality tabs.
 */

import { createServerFn } from '@tanstack/react-start'

import type {
  CheckExecution,
  QualityCheck,
  QualityOverview,
  RecentCheckExecution,
} from './quality.types'

import { fetchQualitySnapshot } from '@/server/quality.dagster'

export type {
  CheckExecution,
  QualityCheck,
  QualityOverview,
  RecentCheckExecution,
} from './quality.types'

const getDagsterUrl = () =>
  process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:3000/graphql'

const ASSET_CHECK_EXECUTIONS_QUERY = `
  query AssetCheckExecutionsQuery($assetKey: AssetKeyInput!, $limit: Int!) {
    assetCheckExecutions(assetKey: $assetKey, limit: $limit) {
      status
      runId
      timestamp
      checkName
      evaluation {
        severity
        metadataEntries {
          __typename
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

type DagsterMetadataEntry =
  | { label: string; __typename: 'TextMetadataEntry'; text: string }
  | { label: string; __typename: 'IntMetadataEntry'; intValue: number }
  | { label: string; __typename: 'FloatMetadataEntry'; floatValue: number }
  | { label: string; __typename: 'BoolMetadataEntry'; boolValue: boolean }
  | { label: string; __typename: string }

function normalizeExecutionStatus(status: string): QualityCheck['status'] {
  const normalized = status.trim().toUpperCase()
  if (normalized === 'SUCCEEDED') return 'PASSED'
  if (normalized === 'FAILED') return 'FAILED'
  if (normalized === 'IN_PROGRESS') return 'IN_PROGRESS'
  return 'SKIPPED'
}

function normalizeSeverity(
  severity: string | null | undefined,
): QualityCheck['severity'] {
  return severity === 'WARN' ? 'WARN' : 'ERROR'
}

function toEpochMs(value: string | number): number {
  if (typeof value === 'number') {
    if (value > 1_000_000_000_000) return value
    return value * 1000
  }
  const trimmed = value.trim()
  if (!trimmed) return 0
  const asNum = Number(trimmed)
  if (!Number.isNaN(asNum) && Number.isFinite(asNum)) {
    if (asNum > 1_000_000_000_000) return asNum
    return asNum * 1000
  }
  const asDateMs = Date.parse(trimmed)
  if (!Number.isNaN(asDateMs)) return asDateMs
  return 0
}

function toIsoTimestamp(value: string | number): string {
  return new Date(toEpochMs(value)).toISOString()
}

function metadataEntriesToRecord(
  entries: Array<DagsterMetadataEntry> | null | undefined,
): Record<string, string | number | boolean | null | undefined> {
  const record: Record<string, string | number | boolean | null | undefined> =
    {}
  if (!entries) return record
  for (const entry of entries) {
    if (!entry.label) continue
    if (entry.__typename === 'TextMetadataEntry' && 'text' in entry) {
      record[entry.label] = entry.text
      continue
    }
    if (entry.__typename === 'IntMetadataEntry' && 'intValue' in entry) {
      record[entry.label] = entry.intValue
      continue
    }
    if (entry.__typename === 'FloatMetadataEntry' && 'floatValue' in entry) {
      record[entry.label] = entry.floatValue
      continue
    }
    if (entry.__typename === 'BoolMetadataEntry' && 'boolValue' in entry) {
      record[entry.label] = entry.boolValue
      continue
    }
  }
  return record
}

/**
 * Get overview of all quality metrics
 */
export const getQualityOverview = createServerFn().handler(
  async (): Promise<QualityOverview | { error: string }> => {
    const snapshot = await fetchQualitySnapshot()
    if ('error' in snapshot) return snapshot

    const evaluated =
      snapshot.passingChecks + snapshot.failingChecks + snapshot.warningChecks
    const qualityScore =
      evaluated > 0
        ? Math.round(
            ((snapshot.passingChecks + snapshot.warningChecks) / evaluated) *
              100,
          )
        : 0

    const categories = [
      {
        category: 'Contract (Pandera)',
        predicate: (check: QualityCheck) => check.name === 'pandera_contract',
      },
      {
        category: 'dbt tests',
        predicate: (check: QualityCheck) => check.name.startsWith('dbt__'),
      },
      {
        category: 'Custom',
        predicate: (check: QualityCheck) =>
          check.name !== 'pandera_contract' && !check.name.startsWith('dbt__'),
      },
    ]

    const byCategory = categories
      .map((category) => {
        const relevant = snapshot.latestChecks.filter(category.predicate)
        if (!relevant.length) return null
        const passing = relevant.filter(
          (check) => check.status === 'PASSED',
        ).length
        const total = relevant.length
        return {
          category: category.category,
          passing,
          total,
          percentage: Math.round((passing / total) * 100),
        }
      })
      .filter(
        (category): category is NonNullable<typeof category> =>
          category !== null,
      )

    return {
      totalChecks: snapshot.totalChecks,
      passingChecks: snapshot.passingChecks,
      failingChecks: snapshot.failingChecks,
      warningChecks: snapshot.warningChecks,
      qualityScore,
      byCategory,
      trend: [],
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
        const response = await fetch(dagsterUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: ASSET_CHECK_EXECUTIONS_QUERY,
            variables: {
              assetKey: { path: assetKey },
              limit: 200,
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
        const newestByCheck = new Map<string, (typeof executions)[number]>()

        for (const exec of executions) {
          const existing = newestByCheck.get(exec.checkName)
          if (!existing) {
            newestByCheck.set(exec.checkName, exec)
            continue
          }
          if (toEpochMs(exec.timestamp) > toEpochMs(existing.timestamp)) {
            newestByCheck.set(exec.checkName, exec)
          }
        }

        return Array.from(newestByCheck.values())
          .map((exec) => {
            const status = normalizeExecutionStatus(exec.status)
            const severity = normalizeSeverity(exec.evaluation?.severity)
            return {
              name: exec.checkName,
              assetKey,
              description: undefined,
              severity,
              status,
              lastExecutionTime: toIsoTimestamp(exec.timestamp),
              lastResult: {
                passed: status === 'PASSED',
                metadata: metadataEntriesToRecord(
                  exec.evaluation?.metadataEntries,
                ),
              },
            } satisfies QualityCheck
          })
          .sort((a, b) => (a.name < b.name ? -1 : 1))
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
      data: { assetKey, checkName, limit = 20 },
    }): Promise<Array<CheckExecution> | { error: string }> => {
      const dagsterUrl = getDagsterUrl()

      try {
        const fetchLimit = Math.max(50, limit * 3)
        const response = await fetch(dagsterUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: ASSET_CHECK_EXECUTIONS_QUERY,
            variables: {
              assetKey: { path: assetKey },
              limit: fetchLimit,
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

        const executions = (result.data?.assetCheckExecutions || []).filter(
          (exec: { checkName: string }) => exec.checkName === checkName,
        )

        executions.sort(
          (
            a: { timestamp: string | number },
            b: { timestamp: string | number },
          ) => toEpochMs(b.timestamp) - toEpochMs(a.timestamp),
        )

        return executions.slice(0, limit).map(
          (exec: {
            timestamp: string | number
            status: string
            runId?: string | null
            evaluation?: {
              metadataEntries?: Array<DagsterMetadataEntry> | null
            } | null
          }) => ({
            timestamp: toIsoTimestamp(exec.timestamp),
            passed: normalizeExecutionStatus(exec.status) === 'PASSED',
            runId: exec.runId ?? undefined,
            metadata: metadataEntriesToRecord(exec.evaluation?.metadataEntries),
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
  async (): Promise<Array<QualityCheck> | { error: string }> => {
    const snapshot = await fetchQualitySnapshot()
    if ('error' in snapshot) return snapshot
    return snapshot.failingChecksList
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
        recentExecutions: Array<RecentCheckExecution>
      }
    | { error: string }
  > => {
    try {
      const [overviewResult, snapshot] = await Promise.all([
        getQualityOverview(),
        fetchQualitySnapshot(),
      ])

      if ('error' in overviewResult) return overviewResult
      if ('error' in snapshot) return snapshot

      return {
        overview: overviewResult,
        failingChecks: snapshot.failingChecksList,
        recentExecutions: snapshot.recentExecutions,
      }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  },
)

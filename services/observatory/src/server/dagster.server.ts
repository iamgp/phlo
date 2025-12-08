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
    const dagsterUrl = process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:10006/graphql'

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
  }
)

/**
 * Get health metrics from Dagster
 */
export const getHealthMetrics = createServerFn().handler(
  async (): Promise<HealthMetrics | { error: string }> => {
    const dagsterUrl = process.env.DAGSTER_GRAPHQL_URL || 'http://localhost:10006/graphql'

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
  }
)

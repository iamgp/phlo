/**
 * Nessie Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { cacheKeys, cacheTTL, withCache } from '@/server/cache'
import { apiGet } from '@/server/phlo-api'

// Types for Nessie data structures
export interface Branch {
  type: 'BRANCH' | 'TAG'
  name: string
  hash: string
}

export interface NessieConfig {
  connected: boolean
  error?: string
  defaultBranch?: string
}

// Python API response types (snake_case)
interface ApiConnectionStatus {
  connected: boolean
  error?: string
  default_branch?: string
}

/**
 * Check if Nessie is reachable
 */
export const checkNessieConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { nessieUrl?: string } = {}) => input)
  .handler(async ({ data }): Promise<NessieConfig> => {
    try {
      const key = cacheKeys.nessieConnection(data.nessieUrl ?? 'default')
      const result = await withCache(
        () => apiGet<ApiConnectionStatus>('/api/nessie/connection'),
        key,
        cacheTTL.nessieConnection,
      )
      return {
        connected: result.connected,
        error: result.error,
        defaultBranch: result.default_branch,
      }
    } catch (error) {
      return {
        connected: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Get all branches and tags
 */
export const getBranches = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { nessieUrl?: string } = {}) => input)
  .handler(async ({ data }): Promise<Array<Branch> | { error: string }> => {
    try {
      const key = cacheKeys.nessieBranches(data.nessieUrl ?? 'default')
      return await withCache(
        () => apiGet<Array<Branch> | { error: string }>('/api/nessie/branches'),
        key,
        cacheTTL.nessieBranches,
      )
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

/**
 * Nessie Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/observatory/api/auth'
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

interface ApiBranch {
  id: string
  name: string
  current?: boolean
  metadata?: Record<string, unknown>
}

interface ApiBranchList {
  items: Array<ApiBranch>
}

function transformBranch(branch: ApiBranch): Branch {
  const hash = branch.metadata?.hash
  return {
    type: 'BRANCH',
    name: branch.name,
    hash: typeof hash === 'string' ? hash : branch.id,
  }
}

/**
 * Check if Nessie is reachable
 */
export const checkNessieConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: Record<string, never> = {}) => input)
  .handler(async (): Promise<NessieConfig> => {
    try {
      const result = await withCache(
        () =>
          apiGet<ApiBranchList | { error: string }>(
            '/api/observatory/branches',
          ),
        cacheKeys.nessieConnection(),
        cacheTTL.nessieConnection,
      )
      if ('error' in result) {
        return { connected: false, error: result.error }
      }
      const current = result.items.find((branch) => branch.current)
      return {
        connected: true,
        defaultBranch: current?.name ?? result.items[0]?.name,
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
  .inputValidator((input: Record<string, never> = {}) => input)
  .handler(async (): Promise<Array<Branch> | { error: string }> => {
    try {
      const result = await withCache(
        () =>
          apiGet<ApiBranchList | { error: string }>(
            '/api/observatory/branches',
          ),
        cacheKeys.nessieBranches(),
        cacheTTL.nessieBranches,
      )
      if ('error' in result) return result
      return result.items.map(transformBranch)
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

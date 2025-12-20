/**
 * Nessie Server Functions
 *
 * Server-side functions for interacting with the Nessie REST API.
 * Enables git-like data versioning features in Observatory.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'

// Types for Nessie data structures
export interface Branch {
  type: 'BRANCH' | 'TAG'
  name: string
  hash: string
}

export interface CommitMeta {
  hash: string
  message: string
  committer: string
  authors: Array<string>
  commitTime: string
  authorTime: string
  parentCommitHashes: Array<string>
}

export interface LogEntry {
  commitMeta: CommitMeta
  parentCommitHash: string
  operations: Array<object> | null
}

export interface NessieConfig {
  connected: boolean
  error?: string
  defaultBranch?: string
}

const DEFAULT_NESSIE_URL = 'http://localhost:19120/api/v2'

function resolveNessieUrl(override?: string): string {
  if (override && override.trim()) return override
  return process.env.NESSIE_URL || DEFAULT_NESSIE_URL
}

/**
 * Check if Nessie is reachable
 */
export const checkNessieConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { nessieUrl?: string } = {}) => input)
  .handler(async ({ data }): Promise<NessieConfig> => {
    const nessieUrl = resolveNessieUrl(data.nessieUrl)

    try {
      const response = await fetch(`${nessieUrl}/config`, {
        signal: AbortSignal.timeout(5000),
      })

      if (!response.ok) {
        return {
          connected: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      const config = await response.json()

      return {
        connected: true,
        defaultBranch: config.defaultBranch || 'main',
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
    const nessieUrl = resolveNessieUrl(data.nessieUrl)

    try {
      const response = await fetch(`${nessieUrl}/trees`, {
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const payload = await response.json()
      return payload.references || []
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  })

/**
 * Get branch details by name
 */
export const getBranch = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { branchName: string; nessieUrl?: string }) => input)
  .handler(async ({ data }): Promise<Branch | { error: string }> => {
    const nessieUrl = resolveNessieUrl(data.nessieUrl)
    const branchName = data.branchName

    try {
      const response = await fetch(
        `${nessieUrl}/trees/${encodeURIComponent(branchName)}`,
        {
          signal: AbortSignal.timeout(5000),
        },
      )

      if (!response.ok) {
        if (response.status === 404) {
          return { error: `Branch '${branchName}' not found` }
        }
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const payload = await response.json()
      return {
        type: payload.type || 'BRANCH',
        name: payload.name,
        hash: payload.hash,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  })

/**
 * Get commit history for a branch
 */
export const getCommits = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { branch: string; limit?: number; nessieUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { branch, limit = 50, nessieUrl: nessieUrlOverride },
    }): Promise<Array<LogEntry> | { error: string }> => {
      const nessieUrl = resolveNessieUrl(nessieUrlOverride)

      try {
        const url = new URL(
          `${nessieUrl}/trees/${encodeURIComponent(branch)}/history`,
        )
        url.searchParams.set('maxRecords', String(limit))

        const response = await fetch(url.toString(), {
          signal: AbortSignal.timeout(10000),
        })

        if (!response.ok) {
          if (response.status === 404) {
            return { error: `Branch '${branch}' not found` }
          }
          return { error: `HTTP ${response.status}: ${response.statusText}` }
        }

        const data = await response.json()
        return data.logEntries || []
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get contents (tables) at a specific branch/ref
 */
export const getContents = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { branch: string; prefix?: string; nessieUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { branch, prefix, nessieUrl: nessieUrlOverride },
    }): Promise<Array<object> | { error: string }> => {
      const nessieUrl = resolveNessieUrl(nessieUrlOverride)

      try {
        const url = new URL(
          `${nessieUrl}/trees/${encodeURIComponent(branch)}/entries`,
        )
        if (prefix) {
          url.searchParams.set(
            'filter',
            `entry.namespace.startsWith('${prefix}')`,
          )
        }

        const response = await fetch(url.toString(), {
          signal: AbortSignal.timeout(10000),
        })

        if (!response.ok) {
          return { error: `HTTP ${response.status}: ${response.statusText}` }
        }

        const data = await response.json()
        return data.entries || []
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Compare two branches (diff)
 */
export const compareBranches = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { fromBranch: string; toBranch: string; nessieUrl?: string }) =>
      input,
  )
  .handler(
    async ({
      data: { fromBranch, toBranch, nessieUrl: nessieUrlOverride },
    }): Promise<object | { error: string }> => {
      const nessieUrl = resolveNessieUrl(nessieUrlOverride)

      try {
        const url = new URL(
          `${nessieUrl}/trees/${encodeURIComponent(toBranch)}/diff/${encodeURIComponent(fromBranch)}`,
        )

        const response = await fetch(url.toString(), {
          signal: AbortSignal.timeout(10000),
        })

        if (!response.ok) {
          return { error: `HTTP ${response.status}: ${response.statusText}` }
        }

        const data = await response.json()
        return data
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Create a new branch
 */
export const createBranch = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { name: string; fromBranch: string; nessieUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { name, fromBranch, nessieUrl: nessieUrlOverride },
    }): Promise<Branch | { error: string }> => {
      const nessieUrl = resolveNessieUrl(nessieUrlOverride)

      try {
        // First get the source branch hash
        const sourceResponse = await fetch(
          `${nessieUrl}/trees/${encodeURIComponent(fromBranch)}`,
          {
            signal: AbortSignal.timeout(5000),
          },
        )

        if (!sourceResponse.ok) {
          return { error: `Source branch '${fromBranch}' not found` }
        }

        const sourceBranch = await sourceResponse.json()

        // Create the new branch
        const createResponse = await fetch(`${nessieUrl}/trees`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'BRANCH',
            name,
            hash: sourceBranch.hash,
          }),
          signal: AbortSignal.timeout(10000),
        })

        if (!createResponse.ok) {
          const errorText = await createResponse.text()
          return { error: `Failed to create branch: ${errorText}` }
        }

        const newBranch = await createResponse.json()
        return {
          type: 'BRANCH',
          name: newBranch.name,
          hash: newBranch.hash,
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Delete a branch
 */
export const deleteBranch = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { name: string; hash: string; nessieUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { name, hash, nessieUrl: nessieUrlOverride },
    }): Promise<{ success: boolean } | { error: string }> => {
      const nessieUrl = resolveNessieUrl(nessieUrlOverride)

      try {
        const url = new URL(`${nessieUrl}/trees/${encodeURIComponent(name)}`)
        url.searchParams.set('expectedHash', hash)

        const response = await fetch(url.toString(), {
          method: 'DELETE',
          signal: AbortSignal.timeout(10000),
        })

        if (!response.ok) {
          const errorText = await response.text()
          return { error: `Failed to delete branch: ${errorText}` }
        }

        return { success: true }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Merge branches
 */
export const mergeBranch = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: {
      fromBranch: string
      intoBranch: string
      message?: string
      nessieUrl?: string
    }) => input,
  )
  .handler(
    async ({
      data: { fromBranch, intoBranch, message, nessieUrl: nessieUrlOverride },
    }): Promise<{ success: boolean; hash?: string } | { error: string }> => {
      const nessieUrl = resolveNessieUrl(nessieUrlOverride)

      try {
        // Get source branch hash
        const sourceResponse = await fetch(
          `${nessieUrl}/trees/${encodeURIComponent(fromBranch)}`,
          {
            signal: AbortSignal.timeout(5000),
          },
        )

        if (!sourceResponse.ok) {
          return { error: `Source branch '${fromBranch}' not found` }
        }

        const sourceBranch = await sourceResponse.json()

        // Get target branch hash
        const targetResponse = await fetch(
          `${nessieUrl}/trees/${encodeURIComponent(intoBranch)}`,
          {
            signal: AbortSignal.timeout(5000),
          },
        )

        if (!targetResponse.ok) {
          return { error: `Target branch '${intoBranch}' not found` }
        }

        const targetBranch = await targetResponse.json()

        // Perform merge
        const url = new URL(
          `${nessieUrl}/trees/${encodeURIComponent(intoBranch)}/history/merge`,
        )
        url.searchParams.set('expectedHash', targetBranch.hash)

        const mergeResponse = await fetch(url.toString(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fromRefName: fromBranch,
            fromHash: sourceBranch.hash,
            message: message || `Merge ${fromBranch} into ${intoBranch}`,
          }),
          signal: AbortSignal.timeout(10000),
        })

        if (!mergeResponse.ok) {
          const errorText = await mergeResponse.text()
          return { error: `Merge failed: ${errorText}` }
        }

        const result = await mergeResponse.json()
        return { success: true, hash: result.resultantTargetHash }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

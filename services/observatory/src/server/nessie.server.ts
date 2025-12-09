/**
 * Nessie Server Functions
 *
 * Server-side functions for interacting with the Nessie REST API.
 * Enables git-like data versioning features in Observatory.
 */

import { createServerFn } from '@tanstack/react-start'

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
  authors: string[]
  commitTime: string
  authorTime: string
  parentCommitHashes: string[]
}

export interface LogEntry {
  commitMeta: CommitMeta
  parentCommitHash: string
  operations: object[] | null
}

export interface NessieConfig {
  connected: boolean
  error?: string
  defaultBranch?: string
}

// Get Nessie URL from environment
const getNessieUrl = () =>
  process.env.NESSIE_URL || 'http://localhost:19120/api/v2'

/**
 * Check if Nessie is reachable
 */
export const checkNessieConnection = createServerFn().handler(
  async (): Promise<NessieConfig> => {
    const nessieUrl = getNessieUrl()

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
  },
)

/**
 * Get all branches and tags
 */
export const getBranches = createServerFn().handler(
  async (): Promise<Branch[] | { error: string }> => {
    const nessieUrl = getNessieUrl()

    try {
      const response = await fetch(`${nessieUrl}/trees`, {
        signal: AbortSignal.timeout(10000),
      })

      if (!response.ok) {
        return { error: `HTTP ${response.status}: ${response.statusText}` }
      }

      const data = await response.json()
      return data.references || []
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Unknown error' }
    }
  },
)

/**
 * Get branch details by name
 */
export const getBranch = createServerFn()
  .inputValidator((input: string) => input)
  .handler(
    async ({ data: branchName }): Promise<Branch | { error: string }> => {
      const nessieUrl = getNessieUrl()

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

        const data = await response.json()
        return {
          type: data.type || 'BRANCH',
          name: data.name,
          hash: data.hash,
        }
      } catch (error) {
        return {
          error: error instanceof Error ? error.message : 'Unknown error',
        }
      }
    },
  )

/**
 * Get commit history for a branch
 */
export const getCommits = createServerFn()
  .inputValidator((input: { branch: string; limit?: number }) => input)
  .handler(
    async ({
      data: { branch, limit = 50 },
    }): Promise<LogEntry[] | { error: string }> => {
      const nessieUrl = getNessieUrl()

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
  .inputValidator((input: { branch: string; prefix?: string }) => input)
  .handler(
    async ({
      data: { branch, prefix },
    }): Promise<object[] | { error: string }> => {
      const nessieUrl = getNessieUrl()

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
  .inputValidator((input: { fromBranch: string; toBranch: string }) => input)
  .handler(
    async ({
      data: { fromBranch, toBranch },
    }): Promise<object | { error: string }> => {
      const nessieUrl = getNessieUrl()

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
  .inputValidator((input: { name: string; fromBranch: string }) => input)
  .handler(
    async ({
      data: { name, fromBranch },
    }): Promise<Branch | { error: string }> => {
      const nessieUrl = getNessieUrl()

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
  .inputValidator((input: { name: string; hash: string }) => input)
  .handler(
    async ({
      data: { name, hash },
    }): Promise<{ success: boolean } | { error: string }> => {
      const nessieUrl = getNessieUrl()

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
  .inputValidator(
    (input: { fromBranch: string; intoBranch: string; message?: string }) =>
      input,
  )
  .handler(
    async ({
      data: { fromBranch, intoBranch, message },
    }): Promise<{ success: boolean; hash?: string } | { error: string }> => {
      const nessieUrl = getNessieUrl()

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

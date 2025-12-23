/**
 * Nessie Server Functions
 *
 * Thin wrappers that forward to phlo-api (Python backend).
 * Preserves SSR while keeping business logic in Python.
 */

import { createServerFn } from '@tanstack/react-start'

import { authMiddleware } from '@/server/auth.server'
import { apiDelete, apiGet, apiPost } from '@/server/phlo-api'

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

// Python API response types (snake_case)
interface ApiConnectionStatus {
  connected: boolean
  error?: string
  default_branch?: string
}

interface ApiCommitMeta {
  hash: string
  message: string
  committer?: string
  authors: Array<string>
  commit_time?: string
  author_time?: string
  parent_commit_hashes: Array<string>
}

interface ApiLogEntry {
  commit_meta: ApiCommitMeta
  parent_commit_hash?: string
  operations?: Array<object>
}

// Transform functions
function transformLogEntry(e: ApiLogEntry): LogEntry {
  return {
    commitMeta: {
      hash: e.commit_meta.hash,
      message: e.commit_meta.message,
      committer: e.commit_meta.committer || '',
      authors: e.commit_meta.authors,
      commitTime: e.commit_meta.commit_time || '',
      authorTime: e.commit_meta.author_time || '',
      parentCommitHashes: e.commit_meta.parent_commit_hashes,
    },
    parentCommitHash: e.parent_commit_hash || '',
    operations: e.operations || null,
  }
}

/**
 * Check if Nessie is reachable
 */
export const checkNessieConnection = createServerFn()
  .middleware([authMiddleware])
  .inputValidator((input: { nessieUrl?: string } = {}) => input)
  .handler(async (): Promise<NessieConfig> => {
    try {
      const result = await apiGet<ApiConnectionStatus>('/api/nessie/connection')
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
  .handler(async (): Promise<Array<Branch> | { error: string }> => {
    try {
      return await apiGet<Array<Branch> | { error: string }>('/api/nessie/branches')
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
  .handler(
    async ({ data: { branchName } }): Promise<Branch | { error: string }> => {
      try {
        return await apiGet<Branch | { error: string }>(
          `/api/nessie/branches/${encodeURIComponent(branchName)}`,
        )
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

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
      data: { branch, limit = 50 },
    }): Promise<Array<LogEntry> | { error: string }> => {
      try {
        const result = await apiGet<Array<ApiLogEntry> | { error: string }>(
          `/api/nessie/branches/${encodeURIComponent(branch)}/history`,
          { limit },
        )

        if ('error' in result) return result
        return result.map(transformLogEntry)
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
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
      data: { branch, prefix },
    }): Promise<Array<object> | { error: string }> => {
      try {
        return await apiGet<Array<object> | { error: string }>(
          `/api/nessie/branches/${encodeURIComponent(branch)}/entries`,
          { prefix },
        )
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

/**
 * Compare two branches (diff)
 */
export const compareBranches = createServerFn()
  .middleware([authMiddleware])
  .inputValidator(
    (input: { fromBranch: string; toBranch: string; nessieUrl?: string }) => input,
  )
  .handler(
    async ({
      data: { fromBranch, toBranch },
    }): Promise<object | { error: string }> => {
      try {
        return await apiGet<object>(
          `/api/nessie/diff/${encodeURIComponent(fromBranch)}/${encodeURIComponent(toBranch)}`,
        )
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
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
      data: { name, fromBranch },
    }): Promise<Branch | { error: string }> => {
      try {
        return await apiPost<Branch | { error: string }>(
          `/api/nessie/branches?name=${encodeURIComponent(name)}&from_branch=${encodeURIComponent(fromBranch)}`,
        )
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
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
      data: { name, hash },
    }): Promise<{ success: boolean } | { error: string }> => {
      try {
        return await apiDelete<{ success: boolean } | { error: string }>(
          `/api/nessie/branches/${encodeURIComponent(name)}`,
          { expected_hash: hash },
        )
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
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
      data: { fromBranch, intoBranch, message },
    }): Promise<{ success: boolean; hash?: string } | { error: string }> => {
      try {
        return await apiPost<{ success: boolean; hash?: string } | { error: string }>(
          `/api/nessie/merge?from_branch=${encodeURIComponent(fromBranch)}&into_branch=${encodeURIComponent(intoBranch)}${message ? `&message=${encodeURIComponent(message)}` : ''}`,
        )
      } catch (error) {
        return { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    },
  )

/**
 * React hook for managing saved queries and views
 */

import { useCallback, useSyncExternalStore } from 'react'

import type {
  CreateQueryInput,
  CreateViewInput,
  SavedQuery,
  SavedView,
} from '@/lib/savedQueries'
import {
  createSavedQuery,
  createSavedView,
  deleteSavedQuery,
  deleteSavedView,
  getSavedQueries,
  getSavedQueryById,
  getSavedViewById,
  getSavedViews,
  updateSavedQuery,
  updateSavedView,
} from '@/lib/savedQueries'

// External store subscription for React 18+
let listeners: Array<() => void> = []

// Cache for stable snapshot references
let cachedQueries: Array<SavedQuery> | null = null
let cachedViews: Array<SavedView> | null = null

function subscribe(callback: () => void): () => void {
  listeners.push(callback)
  return () => {
    listeners = listeners.filter((l) => l !== callback)
  }
}

function notifyListeners(): void {
  // Invalidate caches before notifying
  cachedQueries = null
  cachedViews = null
  listeners.forEach((l) => l())
}

// Wrap mutations to notify listeners
function withNotify<T>(fn: () => T): T {
  const result = fn()
  notifyListeners()
  return result
}

// Snapshot functions - return cached references for stability
function getQueriesSnapshot(): Array<SavedQuery> {
  if (cachedQueries === null) {
    cachedQueries = getSavedQueries()
  }
  return cachedQueries
}

function getViewsSnapshot(): Array<SavedView> {
  if (cachedViews === null) {
    cachedViews = getSavedViews()
  }
  return cachedViews
}

function getServerSnapshot(): Array<SavedQuery> | Array<SavedView> {
  return []
}

/**
 * Hook for managing saved queries
 */
export function useSavedQueries() {
  const queries = useSyncExternalStore(
    subscribe,
    getQueriesSnapshot,
    () => getServerSnapshot() as Array<SavedQuery>,
  )

  const save = useCallback((input: CreateQueryInput): SavedQuery => {
    return withNotify(() => createSavedQuery(input))
  }, [])

  const update = useCallback(
    (
      id: string,
      updates: Partial<Omit<SavedQuery, 'id' | 'createdAt'>>,
    ): SavedQuery | undefined => {
      return withNotify(() => updateSavedQuery(id, updates))
    },
    [],
  )

  const remove = useCallback((id: string): boolean => {
    return withNotify(() => deleteSavedQuery(id))
  }, [])

  const getById = useCallback((id: string): SavedQuery | undefined => {
    return getSavedQueryById(id)
  }, [])

  return {
    queries,
    saveQuery: save,
    updateQuery: update,
    deleteQuery: remove,
    getQueryById: getById,
  }
}

/**
 * Hook for managing saved views
 */
export function useSavedViews() {
  const views = useSyncExternalStore(
    subscribe,
    getViewsSnapshot,
    () => getServerSnapshot() as Array<SavedView>,
  )

  const save = useCallback((input: CreateViewInput): SavedView => {
    return withNotify(() => createSavedView(input))
  }, [])

  const update = useCallback(
    (
      id: string,
      updates: Partial<Omit<SavedView, 'id' | 'createdAt'>>,
    ): SavedView | undefined => {
      return withNotify(() => updateSavedView(id, updates))
    },
    [],
  )

  const remove = useCallback((id: string): boolean => {
    return withNotify(() => deleteSavedView(id))
  }, [])

  const getById = useCallback((id: string): SavedView | undefined => {
    return getSavedViewById(id)
  }, [])

  return {
    views,
    saveView: save,
    updateView: update,
    deleteView: remove,
    getViewById: getById,
  }
}

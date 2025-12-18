/**
 * React hook for managing bookmarks
 */

import { useCallback, useSyncExternalStore } from 'react'

import type { Bookmark, CreateBookmarkInput } from '@/lib/savedQueries'
import {
  bookmarkTable,
  createBookmark,
  deleteBookmark,
  deleteBookmarkByTarget,
  getBookmarks,
  getBookmarksByType,
  isBookmarked,
  isTableBookmarked,
  unbookmarkTable,
} from '@/lib/savedQueries'

// External store subscription for React 18+
let listeners: Array<() => void> = []

function subscribe(callback: () => void): () => void {
  listeners.push(callback)
  return () => {
    listeners = listeners.filter((l) => l !== callback)
  }
}

function notifyListeners(): void {
  listeners.forEach((l) => l())
}

// Wrap mutations to notify listeners
function withNotify<T>(fn: () => T): T {
  const result = fn()
  notifyListeners()
  return result
}

// Snapshot function
function getBookmarksSnapshot(): Array<Bookmark> {
  return getBookmarks()
}

function getServerSnapshot(): Array<Bookmark> {
  return []
}

/**
 * Hook for managing bookmarks
 */
export function useBookmarks() {
  const bookmarks = useSyncExternalStore(
    subscribe,
    getBookmarksSnapshot,
    getServerSnapshot,
  )

  const add = useCallback((input: CreateBookmarkInput): Bookmark => {
    return withNotify(() => createBookmark(input))
  }, [])

  const remove = useCallback((id: string): boolean => {
    return withNotify(() => deleteBookmark(id))
  }, [])

  const removeByTarget = useCallback(
    (type: Bookmark['type'], targetId: string): boolean => {
      return withNotify(() => deleteBookmarkByTarget(type, targetId))
    },
    [],
  )

  const checkIsBookmarked = useCallback(
    (type: Bookmark['type'], targetId: string): boolean => {
      return isBookmarked(type, targetId)
    },
    [],
  )

  const filterByType = useCallback((type: Bookmark['type']): Array<Bookmark> => {
    return getBookmarksByType(type)
  }, [])

  return {
    bookmarks,
    addBookmark: add,
    removeBookmark: remove,
    removeBookmarkByTarget: removeByTarget,
    isBookmarked: checkIsBookmarked,
    getBookmarksByType: filterByType,
  }
}

/**
 * Hook for table-specific bookmarks (convenience wrapper)
 */
export function useTableBookmarks() {
  const { bookmarks } = useBookmarks()

  const tableBookmarks = bookmarks.filter((b) => b.type === 'table')

  const toggle = useCallback(
    (
      catalog: string,
      schema: string,
      table: string,
      label?: string,
    ): boolean => {
      const isCurrentlyBookmarked = isTableBookmarked(catalog, schema, table)
      if (isCurrentlyBookmarked) {
        return withNotify(() => unbookmarkTable(catalog, schema, table))
      } else {
        withNotify(() => bookmarkTable(catalog, schema, table, label))
        return true
      }
    },
    [],
  )

  const check = useCallback(
    (catalog: string, schema: string, table: string): boolean => {
      return isTableBookmarked(catalog, schema, table)
    },
    [],
  )

  return {
    tableBookmarks,
    toggleTableBookmark: toggle,
    isTableBookmarked: check,
  }
}

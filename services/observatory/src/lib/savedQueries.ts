/**
 * Saved Queries & Bookmarks Storage
 *
 * localStorage-based persistence for saved queries, views, and bookmarks.
 * Uses versioned schema for future migration support.
 */

import { ulid } from 'ulid'
import { z } from 'zod'

// Storage keys
const SAVED_QUERIES_KEY = 'phlo-observatory-saved-queries-v1'
const BOOKMARKS_KEY = 'phlo-observatory-bookmarks-v1'

// Schemas
const savedQuerySchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  query: z.string().min(1),
  description: z.string().optional(),
  tags: z.array(z.string()).optional(),
  branch: z.string().optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

const savedViewSchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  tableRef: z.object({
    catalog: z.string(),
    schema: z.string(),
    table: z.string(),
  }),
  columns: z.array(z.string()).optional(),
  filters: z.string().optional(),
  sortBy: z
    .object({
      column: z.string(),
      direction: z.enum(['asc', 'desc']),
    })
    .optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

const bookmarkSchema = z.object({
  id: z.string(),
  type: z.enum(['table', 'query', 'view']),
  targetId: z.string(),
  label: z.string().optional(),
  createdAt: z.string(),
})

const savedQueriesStoreSchema = z.object({
  version: z.literal(1),
  queries: z.array(savedQuerySchema),
  views: z.array(savedViewSchema),
})

const bookmarksStoreSchema = z.object({
  version: z.literal(1),
  bookmarks: z.array(bookmarkSchema),
})

// Types
export type SavedQuery = z.infer<typeof savedQuerySchema>
export type SavedView = z.infer<typeof savedViewSchema>
export type Bookmark = z.infer<typeof bookmarkSchema>

type SavedQueriesStore = z.infer<typeof savedQueriesStoreSchema>
type BookmarksStore = z.infer<typeof bookmarksStoreSchema>

// Create inputs (without generated fields)
export type CreateQueryInput = Omit<
  SavedQuery,
  'id' | 'createdAt' | 'updatedAt'
>
export type CreateViewInput = Omit<SavedView, 'id' | 'createdAt' | 'updatedAt'>
export type CreateBookmarkInput = Omit<Bookmark, 'id' | 'createdAt'>

// Helper functions
function getEmptyQueriesStore(): SavedQueriesStore {
  return { version: 1, queries: [], views: [] }
}

function getEmptyBookmarksStore(): BookmarksStore {
  return { version: 1, bookmarks: [] }
}

function loadQueriesStore(): SavedQueriesStore {
  if (typeof window === 'undefined') return getEmptyQueriesStore()

  const raw = window.localStorage.getItem(SAVED_QUERIES_KEY)
  if (!raw) return getEmptyQueriesStore()

  try {
    const parsed = savedQueriesStoreSchema.safeParse(JSON.parse(raw))
    return parsed.success ? parsed.data : getEmptyQueriesStore()
  } catch {
    return getEmptyQueriesStore()
  }
}

function saveQueriesStore(store: SavedQueriesStore): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SAVED_QUERIES_KEY, JSON.stringify(store))
}

function loadBookmarksStore(): BookmarksStore {
  if (typeof window === 'undefined') return getEmptyBookmarksStore()

  const raw = window.localStorage.getItem(BOOKMARKS_KEY)
  if (!raw) return getEmptyBookmarksStore()

  try {
    const parsed = bookmarksStoreSchema.safeParse(JSON.parse(raw))
    return parsed.success ? parsed.data : getEmptyBookmarksStore()
  } catch {
    return getEmptyBookmarksStore()
  }
}

function saveBookmarksStore(store: BookmarksStore): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(BOOKMARKS_KEY, JSON.stringify(store))
}

// Saved Queries CRUD
export function getSavedQueries(): Array<SavedQuery> {
  return loadQueriesStore().queries
}

export function getSavedQueryById(id: string): SavedQuery | undefined {
  return getSavedQueries().find((q) => q.id === id)
}

export function createSavedQuery(input: CreateQueryInput): SavedQuery {
  const store = loadQueriesStore()
  const now = new Date().toISOString()
  const query: SavedQuery = {
    ...input,
    id: ulid(),
    createdAt: now,
    updatedAt: now,
  }
  store.queries.push(query)
  saveQueriesStore(store)
  return query
}

export function updateSavedQuery(
  id: string,
  updates: Partial<Omit<SavedQuery, 'id' | 'createdAt'>>,
): SavedQuery | undefined {
  const store = loadQueriesStore()
  const index = store.queries.findIndex((q) => q.id === id)
  if (index === -1) return undefined

  store.queries[index] = {
    ...store.queries[index],
    ...updates,
    updatedAt: new Date().toISOString(),
  }
  saveQueriesStore(store)
  return store.queries[index]
}

export function deleteSavedQuery(id: string): boolean {
  const store = loadQueriesStore()
  const initialLength = store.queries.length
  store.queries = store.queries.filter((q) => q.id !== id)
  if (store.queries.length < initialLength) {
    saveQueriesStore(store)
    return true
  }
  return false
}

// Saved Views CRUD
export function getSavedViews(): Array<SavedView> {
  return loadQueriesStore().views
}

export function getSavedViewById(id: string): SavedView | undefined {
  return getSavedViews().find((v) => v.id === id)
}

export function createSavedView(input: CreateViewInput): SavedView {
  const store = loadQueriesStore()
  const now = new Date().toISOString()
  const view: SavedView = {
    ...input,
    id: ulid(),
    createdAt: now,
    updatedAt: now,
  }
  store.views.push(view)
  saveQueriesStore(store)
  return view
}

export function updateSavedView(
  id: string,
  updates: Partial<Omit<SavedView, 'id' | 'createdAt'>>,
): SavedView | undefined {
  const store = loadQueriesStore()
  const index = store.views.findIndex((v) => v.id === id)
  if (index === -1) return undefined

  store.views[index] = {
    ...store.views[index],
    ...updates,
    updatedAt: new Date().toISOString(),
  }
  saveQueriesStore(store)
  return store.views[index]
}

export function deleteSavedView(id: string): boolean {
  const store = loadQueriesStore()
  const initialLength = store.views.length
  store.views = store.views.filter((v) => v.id !== id)
  if (store.views.length < initialLength) {
    saveQueriesStore(store)
    return true
  }
  return false
}

// Bookmarks CRUD
export function getBookmarks(): Array<Bookmark> {
  return loadBookmarksStore().bookmarks
}

export function getBookmarksByType(type: Bookmark['type']): Array<Bookmark> {
  return getBookmarks().filter((b) => b.type === type)
}

export function isBookmarked(
  type: Bookmark['type'],
  targetId: string,
): boolean {
  return getBookmarks().some((b) => b.type === type && b.targetId === targetId)
}

export function createBookmark(input: CreateBookmarkInput): Bookmark {
  // Prevent duplicates
  if (isBookmarked(input.type, input.targetId)) {
    const existing = getBookmarks().find(
      (b) => b.type === input.type && b.targetId === input.targetId,
    )
    if (existing) return existing
  }

  const store = loadBookmarksStore()
  const bookmark: Bookmark = {
    ...input,
    id: ulid(),
    createdAt: new Date().toISOString(),
  }
  store.bookmarks.push(bookmark)
  saveBookmarksStore(store)
  return bookmark
}

export function deleteBookmark(id: string): boolean {
  const store = loadBookmarksStore()
  const initialLength = store.bookmarks.length
  store.bookmarks = store.bookmarks.filter((b) => b.id !== id)
  if (store.bookmarks.length < initialLength) {
    saveBookmarksStore(store)
    return true
  }
  return false
}

export function deleteBookmarkByTarget(
  type: Bookmark['type'],
  targetId: string,
): boolean {
  const store = loadBookmarksStore()
  const initialLength = store.bookmarks.length
  store.bookmarks = store.bookmarks.filter(
    (b) => !(b.type === type && b.targetId === targetId),
  )
  if (store.bookmarks.length < initialLength) {
    saveBookmarksStore(store)
    return true
  }
  return false
}

// Table bookmark helpers (convenience functions)
export function getTableBookmarkId(
  catalog: string,
  schema: string,
  table: string,
): string {
  return `${catalog}.${schema}.${table}`
}

export function bookmarkTable(
  catalog: string,
  schema: string,
  table: string,
  label?: string,
): Bookmark {
  const targetId = getTableBookmarkId(catalog, schema, table)
  return createBookmark({ type: 'table', targetId, label: label ?? table })
}

export function unbookmarkTable(
  catalog: string,
  schema: string,
  table: string,
): boolean {
  const targetId = getTableBookmarkId(catalog, schema, table)
  return deleteBookmarkByTarget('table', targetId)
}

export function isTableBookmarked(
  catalog: string,
  schema: string,
  table: string,
): boolean {
  const targetId = getTableBookmarkId(catalog, schema, table)
  return isBookmarked('table', targetId)
}

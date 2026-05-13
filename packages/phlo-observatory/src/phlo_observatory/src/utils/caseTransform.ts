/**
 * Utility for converting between snake_case and camelCase.
 * Used to transform API responses to TypeScript conventions.
 */

/**
 * Convert a snake_case string to camelCase
 * Handles SCREAMING_SNAKE_CASE and digits (e.g., column_1 -> column1)
 */
function snakeToCamel(str: string): string {
  return str
    .toLowerCase()
    .replace(/_([a-z0-9])/g, (_, char) => char.toUpperCase())
}

/**
 * Check if value is a special object that should not be transformed
 */
function isSpecialObject(obj: unknown): boolean {
  return (
    obj instanceof Date ||
    obj instanceof Map ||
    obj instanceof Set ||
    obj instanceof RegExp ||
    obj instanceof ArrayBuffer ||
    ArrayBuffer.isView(obj)
  )
}

/** Keys that could cause prototype pollution and should be filtered out */
const DANGEROUS_KEYS = new Set(['__proto__', 'constructor', 'prototype'])

/**
 * Recursively convert all keys in an object from snake_case to camelCase
 * Preserves special objects (Date, Map, Set, RegExp, ArrayBuffer, TypedArrays)
 * Filters out dangerous keys that could cause prototype pollution
 */
export function camelizeKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((item) => camelizeKeys(item)) as T
  }

  if (obj !== null && typeof obj === 'object') {
    if (isSpecialObject(obj)) {
      return obj as T
    }

    const entries: Array<[string, unknown]> = []
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      if (!DANGEROUS_KEYS.has(key)) {
        entries.push([snakeToCamel(key), camelizeKeys(value)])
      }
    }
    return Object.fromEntries(entries) as T
  }

  return obj as T
}

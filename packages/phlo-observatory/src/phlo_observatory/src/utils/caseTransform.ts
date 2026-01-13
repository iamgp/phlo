/**
 * Utility for converting between snake_case and camelCase.
 * Used to transform API responses to TypeScript conventions.
 */

/**
 * Convert a snake_case string to camelCase
 * Handles SCREAMING_SNAKE_CASE and digits (e.g., column_1 -> column1)
 */
export function snakeToCamel(str: string): string {
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

/**
 * Recursively convert all keys in an object from snake_case to camelCase
 * Preserves special objects (Date, Map, Set, RegExp, ArrayBuffer, TypedArrays)
 */
export function camelizeKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((item) => camelizeKeys(item)) as T
  }

  if (obj !== null && typeof obj === 'object') {
    if (isSpecialObject(obj)) {
      return obj as T
    }

    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([key, value]) => [
        snakeToCamel(key),
        camelizeKeys(value),
      ]),
    ) as T
  }

  return obj as T
}

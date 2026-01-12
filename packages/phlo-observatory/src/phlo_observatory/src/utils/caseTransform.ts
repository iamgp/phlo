/**
 * Utility for converting between snake_case and camelCase.
 * Used to transform API responses to TypeScript conventions.
 */

/**
 * Convert a snake_case string to camelCase
 */
export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

/**
 * Recursively convert all keys in an object from snake_case to camelCase
 */
export function camelizeKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((item) => camelizeKeys(item)) as T
  }

  if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([key, value]) => [
        snakeToCamel(key),
        camelizeKeys(value),
      ]),
    ) as T
  }

  return obj as T
}

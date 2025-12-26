/**
 * Phlo API Server Client
 *
 * Helper for server functions to call the Python phlo-api backend.
 * Handles URL resolution for both Docker and local dev environments.
 */

const PHLO_API_URL = process.env.PHLO_API_URL || 'http://localhost:4000'

/**
 * Make a GET request to phlo-api
 */
export async function apiGet<T>(
  endpoint: string,
  params?: Record<string, string | number | boolean | undefined>,
  timeoutMs = 30000,
): Promise<T> {
  const url = new URL(`${PHLO_API_URL}${endpoint}`)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const response = await fetch(url.toString(), {
    signal: AbortSignal.timeout(timeoutMs),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`phlo-api error: ${response.status} ${text}`)
  }

  return response.json()
}

/**
 * Make a POST request to phlo-api
 */
export async function apiPost<T>(
  endpoint: string,
  body?: unknown,
  timeoutMs = 30000,
): Promise<T> {
  const response = await fetch(`${PHLO_API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(timeoutMs),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`phlo-api error: ${response.status} ${text}`)
  }

  return response.json()
}

/**
 * Make a DELETE request to phlo-api
 */
export async function apiDelete<T>(
  endpoint: string,
  params?: Record<string, string>,
  timeoutMs = 30000,
): Promise<T> {
  const url = new URL(`${PHLO_API_URL}${endpoint}`)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value)
    }
  }

  const response = await fetch(url.toString(), {
    method: 'DELETE',
    signal: AbortSignal.timeout(timeoutMs),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`phlo-api error: ${response.status} ${text}`)
  }

  return response.json()
}
